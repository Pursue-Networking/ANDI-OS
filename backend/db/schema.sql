-- =============================================================================
-- ANDI BACKEND SCHEMA v0 (PROTOTYPE)
-- Everything downstream of "we received a gmail message" lives here.
--
-- Layers:
--   RAW       raw_emails, calendar_events, linkedin_records
--   IDENTITY  users, email_accounts, contacts, contact_identifiers
--   DERIVED   envelope_observations, interactions, network_scores, signals
--   PRODUCT   briefs, dossiers, drafts, voice_profiles
--   LEARNING  noise_labels, feedback_events, memory_refs, embeddings
--   OPS       pipeline_runs, processing_cursors
--
-- Postgres 17 + pgvector. Applied automatically by docker compose on first
-- boot of a fresh volume. Reset with: docker compose down -v
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- IDENTITY AND ACCOUNTS
-- ---------------------------------------------------------------------------

-- The product owner. One row per human using ANDI.
CREATE TABLE users (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email       text NOT NULL UNIQUE,
    full_name   text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- A connected mailbox. One user can connect several.
CREATE TABLE email_accounts (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider      text NOT NULL DEFAULT 'gmail' CHECK (provider IN ('gmail', 'outlook')),
    email_address text NOT NULL,
    display_name  text NOT NULL DEFAULT '',
    status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'revoked')),
    connected_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, email_address)
);

-- ---------------------------------------------------------------------------
-- RAW LAYER. Source records land here exactly as received, then never change.
-- ---------------------------------------------------------------------------

-- One row per Gmail message. Field names follow the Gmail MVP backend
-- (GmailMessageFull in ABSOLV/REPOS/Gmail-mcp-backend/src/types/gmail-read.ts)
-- so swapping the dummy ingest for the real MCP sync is a drop-in change.
CREATE TABLE raw_emails (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id        uuid NOT NULL REFERENCES email_accounts(id) ON DELETE CASCADE,
    gmail_message_id  text NOT NULL,
    gmail_thread_id   text NOT NULL,
    message_id_header text NOT NULL DEFAULT '',
    in_reply_to       text NOT NULL DEFAULT '',
    direction         text NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    from_email        text NOT NULL,
    from_name         text NOT NULL DEFAULT '',
    to_emails         text[] NOT NULL DEFAULT '{}',
    cc_emails         text[] NOT NULL DEFAULT '{}',
    subject           text NOT NULL DEFAULT '',
    snippet           text NOT NULL DEFAULT '',
    body_text         text NOT NULL DEFAULT '',
    body_html         text NOT NULL DEFAULT '',
    labels            text[] NOT NULL DEFAULT '{}',
    -- Raw RFC headers we care about for noise detection:
    -- List-Unsubscribe, Precedence, Auto-Submitted, X-Mailer, Feedback-ID ...
    headers           jsonb NOT NULL DEFAULT '{}',
    internal_date     timestamptz NOT NULL,
    ingested_at       timestamptz NOT NULL DEFAULT now(),
    processed         boolean NOT NULL DEFAULT false,
    UNIQUE (account_id, gmail_message_id)
);

CREATE INDEX idx_raw_emails_unprocessed ON raw_emails (user_id) WHERE processed = false;
CREATE INDEX idx_raw_emails_from ON raw_emails (user_id, from_email);
CREATE INDEX idx_raw_emails_thread ON raw_emails (gmail_thread_id, internal_date);

-- One row per calendar event.
CREATE TABLE calendar_events (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id        uuid NOT NULL REFERENCES email_accounts(id) ON DELETE CASCADE,
    provider_event_id text NOT NULL,
    title             text NOT NULL DEFAULT '',
    description       text NOT NULL DEFAULT '',
    starts_at         timestamptz NOT NULL,
    ends_at           timestamptz,
    organizer_email   text NOT NULL DEFAULT '',
    -- [{"email": "...", "name": "...", "response": "accepted"}]
    attendees         jsonb NOT NULL DEFAULT '[]',
    location          text NOT NULL DEFAULT '',
    status            text NOT NULL DEFAULT 'confirmed',
    ingested_at       timestamptz NOT NULL DEFAULT now(),
    processed         boolean NOT NULL DEFAULT false,
    UNIQUE (account_id, provider_event_id)
);

-- One row per person in the LinkedIn connections export CSV.
CREATE TABLE linkedin_records (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name    text NOT NULL,
    url          text NOT NULL DEFAULT '',
    email        text NOT NULL DEFAULT '',
    company      text NOT NULL DEFAULT '',
    position     text NOT NULL DEFAULT '',
    connected_on date,
    source       text NOT NULL DEFAULT 'export',
    ingested_at  timestamptz NOT NULL DEFAULT now(),
    processed    boolean NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------------
-- IDENTITY RESOLUTION. One canonical row per real-world person.
-- ---------------------------------------------------------------------------

CREATE TABLE contacts (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name         text NOT NULL DEFAULT '',
    primary_email        text NOT NULL,
    company              text NOT NULL DEFAULT '',
    title                text NOT NULL DEFAULT '',
    linkedin_url         text NOT NULL DEFAULT '',
    -- 1 = inner circle, 2 = active, 3 = long tail
    tier                 smallint NOT NULL DEFAULT 3 CHECK (tier IN (1, 2, 3)),
    is_user_self         boolean NOT NULL DEFAULT false,
    -- Noise verdict for the PERSON (aggregated from per-email observations).
    -- unknown  = not yet judged
    -- real     = a human worth ranking
    -- noise    = bot, newsletter, transactional, mass marketing
    -- review   = rules and LLM disagree or low confidence, needs a human
    noise_status         text NOT NULL DEFAULT 'unknown' CHECK (noise_status IN ('unknown', 'real', 'noise', 'review')),
    noise_score          real NOT NULL DEFAULT 0.5,     -- 0 = surely real, 1 = surely noise
    noise_reasons        jsonb NOT NULL DEFAULT '[]',
    relationship_summary text NOT NULL DEFAULT '',
    first_seen_at        timestamptz,
    last_interaction_at  timestamptz,
    last_inbound_at      timestamptz,
    last_outbound_at     timestamptz,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, primary_email)
);

CREATE INDEX idx_contacts_noise ON contacts (user_id, noise_status);
CREATE INDEX idx_contacts_last ON contacts (user_id, last_interaction_at DESC);

-- Alternate emails, LinkedIn URLs and name aliases that map to a contact.
CREATE TABLE contact_identifiers (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    kind       text NOT NULL CHECK (kind IN ('email', 'linkedin_url', 'name_alias')),
    value      text NOT NULL,
    UNIQUE (user_id, kind, value)
);

-- ---------------------------------------------------------------------------
-- DERIVED LAYER. Everything here is recomputable from RAW.
-- ---------------------------------------------------------------------------

-- NOISE DETECTION FEATURE STORE. One row per raw email. This is the main
-- working surface for the noise / sender validation system.
-- features keys written by backend.app.noise.rules.extract_envelope_features:
--   has_list_unsubscribe, precedence_bulk, auto_submitted, noreply_sender,
--   transactional_sender, marketing_subject, contains_unsubscribe_text,
--   recipient_count, html_only, user_first_name_in_body, is_reply_in_thread,
--   sender_in_linkedin, prior_outbound_to_sender
CREATE TABLE envelope_observations (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_email_id   uuid NOT NULL UNIQUE REFERENCES raw_emails(id) ON DELETE CASCADE,
    sender_email   text NOT NULL,
    features       jsonb NOT NULL DEFAULT '{}',
    rule_score     real NOT NULL,                 -- 0 real .. 1 noise
    rule_verdict   text NOT NULL CHECK (rule_verdict IN ('real', 'noise', 'uncertain')),
    llm_verdict    text CHECK (llm_verdict IN ('real', 'noise', 'uncertain')),
    llm_confidence real,
    llm_reason     text,
    final_verdict  text NOT NULL CHECK (final_verdict IN ('real', 'noise', 'uncertain')),
    decided_by     text NOT NULL CHECK (decided_by IN ('rules', 'llm', 'human')),
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_envelope_verdict ON envelope_observations (user_id, final_verdict);
CREATE INDEX idx_envelope_sender ON envelope_observations (user_id, sender_email);

-- Normalized timeline. One row per touch between the user and a contact.
CREATE TABLE interactions (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id   uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    kind         text NOT NULL CHECK (kind IN ('email_in', 'email_out', 'meeting', 'linkedin_msg')),
    occurred_at  timestamptz NOT NULL,
    source_table text NOT NULL,                    -- raw_emails | calendar_events | linkedin_records
    source_id    uuid NOT NULL,
    snippet      text NOT NULL DEFAULT '',
    meta         jsonb NOT NULL DEFAULT '{}',
    UNIQUE (contact_id, kind, source_id)
);

CREATE INDEX idx_interactions_contact ON interactions (contact_id, occurred_at DESC);
CREATE INDEX idx_interactions_user ON interactions (user_id, occurred_at DESC);

-- Ranking output. Append-only, newest row per contact wins.
CREATE TABLE network_scores (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id    uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    score         real NOT NULL,                  -- 0..100
    -- {"recency": 0.8, "frequency": 0.4, "tier_weight": 1.0, "signal_boost": 0.3, "noise_penalty": 0.0}
    factors       jsonb NOT NULL DEFAULT '{}',
    model_version text NOT NULL DEFAULT 'det-v0',
    computed_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_scores_contact ON network_scores (contact_id, computed_at DESC);
CREATE INDEX idx_scores_user ON network_scores (user_id, computed_at DESC);

-- Reasons to act now. Detected deterministically from interactions.
CREATE TABLE signals (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id  uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    type        text NOT NULL CHECK (type IN (
                    'no_reply_inbound',    -- they wrote, user never answered
                    'no_followup_meeting', -- meeting happened, no email after it
                    'gone_quiet',          -- important contact, long silence
                    'waiting_on_them',     -- user wrote, they never answered
                    'new_intro'            -- fresh first-time warm contact
                )),
    status      text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'used', 'dismissed', 'expired')),
    -- Evidence must cite raw record ids so every claim is checkable.
    evidence    jsonb NOT NULL DEFAULT '{}',
    detected_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contact_id, type, status)
);

CREATE INDEX idx_signals_open ON signals (user_id, status);

-- ---------------------------------------------------------------------------
-- PRODUCT LAYER. What the frontend renders.
-- ---------------------------------------------------------------------------

-- The morning brief. One per user per day.
CREATE TABLE briefs (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brief_date    date NOT NULL,
    content_md    text NOT NULL,
    -- [{"contact_id": "...", "reason": "...", "citations": ["raw_email:uuid", "signal:uuid"]}]
    items         jsonb NOT NULL DEFAULT '[]',
    model_version text NOT NULL DEFAULT '',
    status        text NOT NULL DEFAULT 'generated' CHECK (status IN ('generated', 'viewed')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, brief_date)
);

-- Per-contact profile page. Latest version only.
CREATE TABLE dossiers (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id    uuid NOT NULL UNIQUE REFERENCES contacts(id) ON DELETE CASCADE,
    content_md    text NOT NULL,
    citations     jsonb NOT NULL DEFAULT '[]',
    model_version text NOT NULL DEFAULT '',
    generated_at  timestamptz NOT NULL DEFAULT now()
);

-- Outreach drafts. ANDI never sends. A human approves or rejects.
CREATE TABLE drafts (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id    uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    signal_id     uuid REFERENCES signals(id) ON DELETE SET NULL,
    subject       text NOT NULL DEFAULT '',
    body_text     text NOT NULL,
    rationale     text NOT NULL DEFAULT '',
    citations     jsonb NOT NULL DEFAULT '[]',
    status        text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'edited', 'rejected', 'sent')),
    user_feedback text NOT NULL DEFAULT '',
    model_version text NOT NULL DEFAULT '',
    created_at    timestamptz NOT NULL DEFAULT now(),
    decided_at    timestamptz
);

CREATE INDEX idx_drafts_status ON drafts (user_id, status);

-- How the user writes. Learned from outbound mail, used by the draft agent.
CREATE TABLE voice_profiles (
    user_id      uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    traits       jsonb NOT NULL DEFAULT '{}',
    sample_count integer NOT NULL DEFAULT 0,
    updated_at   timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- LEARNING LAYER. Human ground truth and long-term memory.
-- ---------------------------------------------------------------------------

-- Human labels for the noise system. This is the training set.
CREATE TABLE noise_labels (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id   uuid REFERENCES contacts(id) ON DELETE CASCADE,
    raw_email_id uuid REFERENCES raw_emails(id) ON DELETE CASCADE,
    label        text NOT NULL CHECK (label IN ('real', 'noise')),
    source       text NOT NULL DEFAULT 'human' CHECK (source IN ('human', 'feedback')),
    note         text NOT NULL DEFAULT '',
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- Every user action on ANDI output. Drives learning and audit.
CREATE TABLE feedback_events (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_kind   text NOT NULL CHECK (subject_kind IN ('draft', 'brief', 'noise', 'contact', 'dossier')),
    subject_id     uuid,
    action         text NOT NULL,                 -- approved | rejected | labeled_real | labeled_noise | dismissed ...
    detail         jsonb NOT NULL DEFAULT '{}',
    synced_to_mem0 boolean NOT NULL DEFAULT false,
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- Local map of Mem0 memory ids so hosted memories stay linked to our rows.
CREATE TABLE memory_refs (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id uuid REFERENCES contacts(id) ON DELETE CASCADE,
    mem_id     text NOT NULL,
    kind       text NOT NULL DEFAULT 'fact' CHECK (kind IN ('fact', 'preference', 'feedback')),
    note       text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Semantic index over real (non-noise) content. NVIDIA nv-embedqa-e5-v5, 1024 dims.
CREATE TABLE embeddings (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_kind     text NOT NULL CHECK (source_kind IN ('raw_email', 'contact_summary', 'dossier')),
    source_id       uuid NOT NULL,
    content_preview text NOT NULL DEFAULT '',
    embedding       vector(1024) NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_kind, source_id)
);

CREATE INDEX idx_embeddings_hnsw ON embeddings USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- OPS LAYER
-- ---------------------------------------------------------------------------

-- One row per pipeline execution, with per-stage counts for debugging.
CREATE TABLE pipeline_runs (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trigger     text NOT NULL DEFAULT 'api' CHECK (trigger IN ('api', 'cron', 'manual')),
    status      text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'ok', 'failed')),
    stage_stats jsonb NOT NULL DEFAULT '{}',
    error       text NOT NULL DEFAULT '',
    started_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
);

-- Incremental sync position per account and source, for the real ingestion later.
CREATE TABLE processing_cursors (
    account_id         uuid NOT NULL REFERENCES email_accounts(id) ON DELETE CASCADE,
    source             text NOT NULL DEFAULT 'gmail',
    last_history_id    text NOT NULL DEFAULT '',
    last_internal_date timestamptz,
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (account_id, source)
);
