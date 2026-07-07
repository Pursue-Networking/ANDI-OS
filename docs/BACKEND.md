# BACKEND

## WHAT THIS IS

A dummy end to end prototype of the ANDI backend, built to validate the architecture before real integrations. All Gmail, Calendar and LinkedIn data comes from `backend/db/seed.sql`. Nothing is ever sent anywhere: ANDI only writes drafts and waits for a human decision.

## STACK

| COMPONENT | CHOICE | NOTES |
| --------- | ------ | ----- |
| API | FastAPI (`backend/app`) | routes under `/v1`, stub auth via `X-API-Key`, `/health` is open |
| Pipeline | LangGraph state graph (`backend/app/agents/graph.py`) | 8 stages, idempotent, every run logged in `pipeline_runs` |
| Database | Postgres 17 + pgvector, container `andi-postgres` | host port 5433, schema in `backend/db/schema.sql` |
| Cache | Redis 7, container `andi-redis` | host port 6380, read cache invalidated on writes |
| Chat LLM | `nvidia/nemotron-3-ultra-550b-a55b` | OpenAI compatible API at `integrate.api.nvidia.com/v1` |
| Embeddings | `nvidia/nv-embedqa-e5-v5`, 1024 dims | stored in the pgvector `embeddings` table |
| Long term memory | Mem0 hosted | local rows linked through `memory_refs` |

## HOW TO RUN

```bash
cp backend/.env.example backend/.env    # fill NVIDIA_API_KEY and MEM0_API_KEY
docker compose up -d                    # fresh volume applies schema.sql and seed.sql automatically
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python -m backend.scripts.run_pipeline              # full pipeline run, prints stage stats
.venv/bin/python -m uvicorn backend.app.main:app --port 8000  # API
.venv/bin/python -m pytest backend/tests                      # deterministic tests, no LLM needed
```

Reset the database with `docker compose down -v && docker compose up -d`.
Every `/v1` request needs the `X-API-Key` header (default `dev-local-key`).
Set `LLM_ENABLED=false` for a fully deterministic run without LLM calls.

## ENVIRONMENT

| VARIABLE | DEFAULT OR EXAMPLE | PURPOSE |
| -------- | ------------------ | ------- |
| `DATABASE_URL` | `postgresql://andi:andi@localhost:5433/andi` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6380/0` | Redis connection |
| `NVIDIA_API_KEY` | required for LLM stages | NVIDIA hosted models |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | OpenAI compatible endpoint |
| `CHAT_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b` | triage, brief, drafts, dossiers |
| `EMBED_MODEL` | `nvidia/nv-embedqa-e5-v5` | embeddings, `EMBED_DIM` is 1024 |
| `MEM0_API_KEY` | required for memory | hosted Mem0 |
| `BACKEND_API_KEY` | `dev-local-key` | shared API key stub |
| `LLM_ENABLED` | `true` | `false` skips all LLM calls |

## PIPELINE

Stages run in this order and each records its stats in `pipeline_runs.stage_stats`:

1. `envelope_rules`: deterministic header and keyword scoring of inbound email, verdict real, noise or uncertain.
2. `llm_triage`: the LLM judges only the uncertain middle.
3. `identity`: resolves real senders to contacts and builds the `interactions` timeline.
4. `signals`: detects `new_intro`, `gone_quiet`, `waiting_on_them`, `no_reply_inbound`, `no_followup_meeting`.
5. `scoring`: deterministic relationship scores into `network_scores`.
6. `embeddings`: embeds real content into pgvector.
7. `brief`: morning brief markdown with citations into `briefs`.
8. `drafts`: outreach drafts for actionable signals, pending human decision.

Human labels always outrank the machine: `POST /v1/noise/label` updates the observation or contact, stores a `noise_labels` training row and pushes the preference to Mem0.

## API

| METHOD | PATH | PURPOSE |
| ------ | ---- | ------- |
| GET | `/health` | liveness plus db, redis, llm and mem0 status |
| POST | `/v1/ingest/gmail` | push raw email batches |
| POST | `/v1/ingest/calendar` | push calendar events |
| POST | `/v1/ingest/linkedin` | push linkedin export rows |
| POST | `/v1/pipeline/run` | trigger a pipeline run |
| GET | `/v1/pipeline/runs` | run history with stage stats |
| GET | `/v1/contacts` | ranked contacts with scores |
| GET | `/v1/contacts/{id}` | contact detail with timeline |
| POST | `/v1/contacts/{id}/dossier` | generate a dossier with the LLM |
| GET | `/v1/noise/review` | uncertain items for human review |
| GET | `/v1/noise/stats` | verdict counts by decider |
| POST | `/v1/noise/label` | human real or noise override |
| GET | `/v1/brief/today` | latest brief for today |
| GET | `/v1/brief/history` | past briefs |
| GET | `/v1/drafts` | draft queue, filter by status |
| POST | `/v1/drafts/{id}/decision` | approve, reject or edit with feedback |

## SCHEMA

21 tables in `backend/db/schema.sql`:

- RAW: `users`, `email_accounts`, `raw_emails`, `calendar_events`, `linkedin_records`, `processing_cursors`
- NOISE: `envelope_observations`, `noise_labels`
- DERIVED: `contacts`, `contact_identifiers`, `interactions`, `signals`, `network_scores`, `embeddings`, `dossiers`, `voice_profiles`
- OUTPUT: `briefs`, `drafts`
- FEEDBACK AND MEMORY: `feedback_events`, `memory_refs`
- OPS: `pipeline_runs`

## VERIFIED 2026-07-07

- Full pipeline run with status ok: 24 raw emails, 19 envelope observations (10 noise by rules, 6 real by rules, 3 real by LLM), 9 contacts, 17 interactions, 12 signals, 36 network scores, 9 embeddings, 1 brief with 5 items, 8 drafts.
- All read endpoints return live data with `X-API-Key`.
- Draft approval flips status, writes `feedback_events` and stores a Mem0 memory.
- Human noise override by `raw_email_id` flips the verdict to `decided_by = 'human'` and lands in `noise_labels`.

## REAL VS FAKE

- Real: schema, pipeline logic, LLM calls, embeddings, Mem0 writes, API surface.
- Fake: all source data (seeded), auth (one shared key), single user, no Google or LinkedIn connection.

## KNOWN LIMITS

- Brief generation runs with think mode off because the NVIDIA gateway times out on long reasoning.
- One shared API key and one seeded user, no OAuth.
- The repo lives on `/mnt/d` under WSL, so filesystem heavy commands are slow.
