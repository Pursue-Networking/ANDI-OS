"""The ANDI pipeline as a LangGraph state machine.

    load context -> envelope rules -> llm triage -> identity resolution
    -> signal detection -> scoring -> embeddings -> morning brief -> drafts

Deterministic stages never depend on the LLM. Every LLM stage degrades
gracefully: if the model is unreachable the run still finishes and the
stats say what was skipped.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .. import cache, db, memory
from ..config import settings
from ..llm import LLMDisabled, chat_json, embed
from ..noise.rules import extract_envelope_features, rule_score
from . import prompts

log = logging.getLogger(__name__)

LLM_CONFIDENCE_FLOOR = 0.6  # below this an llm verdict stays 'uncertain'
TRIAGE_BATCH_LIMIT = 12     # max llm triage calls per run
DRAFT_LIMIT = 3             # max new drafts per run


class PipelineState(TypedDict, total=False):
    user_id: str
    run_id: str
    llm: bool
    stats: dict


def _merge(state: PipelineState, key: str, value) -> dict:
    return {"stats": {**state.get("stats", {}), key: value}}


def _user_context(user_id: str) -> dict:
    user = db.q1("SELECT full_name FROM users WHERE id = %s", (user_id,))
    first_name = (user["full_name"].split()[0] if user and user["full_name"] else "")
    linkedin = db.q("SELECT lower(email) AS email FROM linkedin_records WHERE user_id = %s AND email <> ''", (user_id,))
    outbound = db.q(
        "SELECT DISTINCT lower(unnest(to_emails)) AS email FROM raw_emails WHERE user_id = %s AND direction = 'outbound'",
        (user_id,),
    )
    self_emails = db.q("SELECT lower(email_address) AS email FROM email_accounts WHERE user_id = %s", (user_id,))
    return {
        "user_first_name": first_name,
        "linkedin_emails": {r["email"] for r in linkedin},
        "outbound_recipients": {r["email"] for r in outbound},
        "self_emails": {r["email"] for r in self_emails},
    }


# ---------------------------------------------------------------------------
# STAGE 1: DETERMINISTIC ENVELOPE RULES
# ---------------------------------------------------------------------------

def envelope_rules_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    ctx = _user_context(user_id)
    emails = db.q(
        "SELECT * FROM raw_emails WHERE user_id = %s AND processed = false AND direction = 'inbound' ORDER BY internal_date",
        (user_id,),
    )
    counts = {"real": 0, "noise": 0, "uncertain": 0}
    for em in emails:
        features = extract_envelope_features(em, ctx)
        score, verdict, reasons = rule_score(features)
        features["_reasons"] = reasons
        db.execute(
            """INSERT INTO envelope_observations
               (user_id, raw_email_id, sender_email, features, rule_score, rule_verdict, final_verdict, decided_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'rules')
               ON CONFLICT (raw_email_id) DO NOTHING""",
            (user_id, em["id"], em["from_email"].lower(), db.jsonb(features), score, verdict, verdict),
        )
        counts[verdict] += 1
    return _merge(state, "envelope_rules", counts)


# ---------------------------------------------------------------------------
# STAGE 2: LLM TRIAGE FOR THE UNCERTAIN MIDDLE
# ---------------------------------------------------------------------------

def llm_triage_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    rows = db.q(
        """SELECT eo.id, eo.features, r.from_email, r.from_name, r.subject, r.body_text
           FROM envelope_observations eo
           JOIN raw_emails r ON r.id = eo.raw_email_id
           WHERE eo.user_id = %s AND eo.final_verdict = 'uncertain' AND eo.llm_verdict IS NULL
           ORDER BY r.internal_date DESC
           LIMIT %s""",
        (user_id, TRIAGE_BATCH_LIMIT),
    )
    if not state.get("llm", True):
        return _merge(state, "llm_triage", {"skipped": "llm disabled", "pending": len(rows)})

    out = {"judged": 0, "kept_uncertain": 0, "errors": 0}
    for row in rows:
        try:
            result = chat_json(
                prompts.NOISE_TRIAGE_SYSTEM,
                prompts.noise_triage_user(row, row["features"]),
                temperature=0.2,
            )
            verdict = str(result.get("verdict", "uncertain")).lower()
            confidence = float(result.get("confidence", 0))
            reason = str(result.get("reason", ""))[:500]
            if verdict not in ("real", "noise", "uncertain"):
                verdict = "uncertain"
            final = verdict if (verdict != "uncertain" and confidence >= LLM_CONFIDENCE_FLOOR) else "uncertain"
            db.execute(
                """UPDATE envelope_observations
                   SET llm_verdict = %s, llm_confidence = %s, llm_reason = %s,
                       final_verdict = %s,
                       decided_by = CASE WHEN %s <> 'uncertain' THEN 'llm' ELSE decided_by END
                   WHERE id = %s""",
                (verdict, confidence, reason, final, final, row["id"]),
            )
            out["judged"] += 1
            if final == "uncertain":
                out["kept_uncertain"] += 1
        except LLMDisabled:
            return _merge(state, "llm_triage", {"skipped": "llm disabled", "pending": len(rows)})
        except Exception as exc:
            log.warning("triage failed for observation %s: %s", row["id"], exc)
            out["errors"] += 1
    return _merge(state, "llm_triage", out)


# ---------------------------------------------------------------------------
# STAGE 3: IDENTITY RESOLUTION
# ---------------------------------------------------------------------------

def _upsert_contact(user_id: str, email: str, name: str = "", noise_status: str = "real") -> str:
    email = email.lower()
    row = db.q1(
        """INSERT INTO contacts (user_id, primary_email, display_name, noise_status)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (user_id, primary_email) DO UPDATE SET
             display_name = CASE WHEN contacts.display_name = '' THEN EXCLUDED.display_name ELSE contacts.display_name END,
             noise_status = CASE
                 WHEN contacts.noise_status = 'unknown' THEN EXCLUDED.noise_status
                 WHEN contacts.noise_status = 'review' AND EXCLUDED.noise_status = 'real' THEN 'real'
                 ELSE contacts.noise_status END,
             updated_at = now()
           RETURNING id""",
        (user_id, email, name or email.split("@")[0], noise_status),
    )
    db.execute(
        "INSERT INTO contact_identifiers (user_id, contact_id, kind, value) VALUES (%s, %s, 'email', %s) ON CONFLICT DO NOTHING",
        (user_id, row["id"], email),
    )
    return str(row["id"])


def identity_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    ctx = _user_context(user_id)
    stats = {"contacts_upserted": 0, "interactions": 0}

    # Inbound senders judged real or uncertain become contacts. Noise never does.
    senders = db.q(
        """SELECT DISTINCT ON (lower(r.from_email)) lower(r.from_email) AS email, r.from_name, eo.final_verdict
           FROM envelope_observations eo JOIN raw_emails r ON r.id = eo.raw_email_id
           WHERE eo.user_id = %s
           ORDER BY lower(r.from_email), r.internal_date DESC""",
        (user_id,),
    )
    email_to_contact: dict[str, str] = {}
    for s in senders:
        if s["final_verdict"] == "noise" or s["email"] in ctx["self_emails"]:
            continue
        status = "real" if s["final_verdict"] == "real" else "review"
        email_to_contact[s["email"]] = _upsert_contact(user_id, s["email"], s["from_name"], status)
        stats["contacts_upserted"] += 1

    # People the user wrote to are real by definition.
    for r in db.q(
        "SELECT DISTINCT lower(unnest(to_emails)) AS email FROM raw_emails WHERE user_id = %s AND direction = 'outbound'",
        (user_id,),
    ):
        if r["email"] in ctx["self_emails"]:
            continue
        email_to_contact[r["email"]] = _upsert_contact(user_id, r["email"], "", "real")

    # LinkedIn connections are real people and enrich existing contacts.
    for li in db.q("SELECT * FROM linkedin_records WHERE user_id = %s", (user_id,)):
        if li["email"]:
            cid = _upsert_contact(user_id, li["email"], li["full_name"], "real")
            email_to_contact[li["email"].lower()] = cid
        db.execute(
            """UPDATE contacts SET
                 company = CASE WHEN company = '' THEN %s ELSE company END,
                 title = CASE WHEN title = '' THEN %s ELSE title END,
                 linkedin_url = CASE WHEN linkedin_url = '' THEN %s ELSE linkedin_url END,
                 display_name = CASE WHEN display_name = '' OR position('@' in display_name) > 0 THEN %s ELSE display_name END
               WHERE user_id = %s AND (lower(primary_email) = lower(%s) OR lower(display_name) = lower(%s))""",
            (li["company"], li["position"], li["url"], li["full_name"], user_id, li["email"] or "", li["full_name"]),
        )
        db.execute("UPDATE linkedin_records SET processed = true WHERE id = %s", (li["id"],))

    # Calendar attendees are real people.
    events = db.q("SELECT * FROM calendar_events WHERE user_id = %s", (user_id,))
    for ev in events:
        for att in ev["attendees"] or []:
            email = str(att.get("email", "")).lower()
            if email and email not in ctx["self_emails"]:
                email_to_contact[email] = _upsert_contact(user_id, email, att.get("name", ""), "real")

    # Interactions: emails.
    for em in db.q("SELECT * FROM raw_emails WHERE user_id = %s AND processed = false", (user_id,)):
        if em["direction"] == "inbound":
            targets = [(em["from_email"].lower(), "email_in")]
        else:
            targets = [(t.lower(), "email_out") for t in em["to_emails"]]
        linked = False
        for email, kind in targets:
            cid = email_to_contact.get(email)
            if not cid:
                continue
            db.execute(
                """INSERT INTO interactions (user_id, contact_id, kind, occurred_at, source_table, source_id, snippet)
                   VALUES (%s, %s, %s, %s, 'raw_emails', %s, %s) ON CONFLICT DO NOTHING""",
                (user_id, cid, kind, em["internal_date"], em["id"], em["snippet"][:300]),
            )
            stats["interactions"] += 1
            linked = True
        # Noise mail and mail to strangers is still marked processed.
        db.execute("UPDATE raw_emails SET processed = true WHERE id = %s", (em["id"],))
        del linked

    # Interactions: meetings.
    for ev in events:
        for att in ev["attendees"] or []:
            cid = email_to_contact.get(str(att.get("email", "")).lower())
            if not cid:
                continue
            db.execute(
                """INSERT INTO interactions (user_id, contact_id, kind, occurred_at, source_table, source_id, snippet)
                   VALUES (%s, %s, 'meeting', %s, 'calendar_events', %s, %s) ON CONFLICT DO NOTHING""",
                (user_id, cid, ev["starts_at"], ev["id"], ev["title"][:300]),
            )
            stats["interactions"] += 1
        db.execute("UPDATE calendar_events SET processed = true WHERE id = %s", (ev["id"],))

    # Roll up timeline aggregates onto contacts.
    db.execute(
        """UPDATE contacts c SET
             first_seen_at = a.first_seen,
             last_interaction_at = a.last_any,
             last_inbound_at = a.last_in,
             last_outbound_at = a.last_out,
             updated_at = now()
           FROM (
             SELECT contact_id,
                    min(occurred_at) AS first_seen,
                    max(occurred_at) AS last_any,
                    max(occurred_at) FILTER (WHERE kind = 'email_in') AS last_in,
                    max(occurred_at) FILTER (WHERE kind = 'email_out') AS last_out
             FROM interactions WHERE user_id = %s GROUP BY contact_id
           ) a
           WHERE c.id = a.contact_id""",
        (user_id,),
    )

    # Simple deterministic tiers.
    db.execute(
        """UPDATE contacts c SET tier = sub.t FROM (
             SELECT c2.id,
               CASE
                 WHEN EXISTS (SELECT 1 FROM interactions i WHERE i.contact_id = c2.id AND i.kind = 'email_in')
                  AND EXISTS (SELECT 1 FROM interactions i WHERE i.contact_id = c2.id AND i.kind = 'email_out') THEN 1
                 WHEN EXISTS (SELECT 1 FROM interactions i WHERE i.contact_id = c2.id AND i.kind = 'meeting')
                  OR c2.linkedin_url <> '' THEN 2
                 ELSE 3
               END AS t
             FROM contacts c2 WHERE c2.user_id = %s AND c2.noise_status IN ('real', 'review')
           ) sub
           WHERE c.id = sub.id""",
        (user_id,),
    )
    return _merge(state, "identity", stats)


# ---------------------------------------------------------------------------
# STAGE 4: SIGNAL DETECTION (reasons to act now)
# ---------------------------------------------------------------------------

def signal_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    found = {"no_reply_inbound": 0, "waiting_on_them": 0, "gone_quiet": 0, "new_intro": 0, "no_followup_meeting": 0}

    def add(contact_id, sig_type, evidence):
        n = db.execute(
            """INSERT INTO signals (user_id, contact_id, type, evidence)
               VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (user_id, contact_id, sig_type, db.jsonb(evidence)),
        )
        found[sig_type] += n

    rows = db.q(
        """WITH last AS (
             SELECT DISTINCT ON (contact_id) contact_id, kind, occurred_at, source_id
             FROM interactions WHERE user_id = %s ORDER BY contact_id, occurred_at DESC
           )
           SELECT c.id AS contact_id, c.first_seen_at, l.kind, l.occurred_at, l.source_id,
                  extract(epoch FROM now() - l.occurred_at) / 86400.0 AS age_days,
                  extract(epoch FROM now() - c.first_seen_at) / 86400.0 AS first_seen_days
           FROM contacts c JOIN last l ON l.contact_id = c.id
           WHERE c.user_id = %s AND c.noise_status = 'real' AND c.is_user_self = false""",
        (user_id, user_id),
    )
    for r in rows:
        age = float(r["age_days"])
        if age > 60:
            add(r["contact_id"], "gone_quiet", {"last_kind": r["kind"], "days_quiet": round(age), "source_id": str(r["source_id"])})
            continue
        if r["kind"] == "email_in" and age > 2:
            add(r["contact_id"], "no_reply_inbound", {"raw_email_id": str(r["source_id"]), "days_waiting": round(age)})
        if r["kind"] == "email_out" and age > 7:
            add(r["contact_id"], "waiting_on_them", {"raw_email_id": str(r["source_id"]), "days_since_sent": round(age)})
        if r["kind"] == "email_in" and float(r["first_seen_days"] or 999) <= 7:
            add(r["contact_id"], "new_intro", {"raw_email_id": str(r["source_id"]), "first_seen_days": round(float(r["first_seen_days"]))})

    meetings = db.q(
        """SELECT i.contact_id, i.source_id, i.occurred_at
           FROM interactions i
           JOIN contacts c ON c.id = i.contact_id AND c.noise_status = 'real'
           WHERE i.user_id = %s AND i.kind = 'meeting'
             AND i.occurred_at BETWEEN now() - interval '30 days' AND now()
             AND NOT EXISTS (
               SELECT 1 FROM interactions o
               WHERE o.contact_id = i.contact_id AND o.kind = 'email_out' AND o.occurred_at > i.occurred_at
             )""",
        (user_id,),
    )
    for m in meetings:
        add(m["contact_id"], "no_followup_meeting", {"calendar_event_id": str(m["source_id"]), "met_at": str(m["occurred_at"])})

    return _merge(state, "signals", found)


# ---------------------------------------------------------------------------
# STAGE 5: DETERMINISTIC SCORING
# ---------------------------------------------------------------------------

def scoring_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    rows = db.q(
        """SELECT c.id, c.tier, c.noise_status,
                  extract(epoch FROM now() - c.last_interaction_at) / 86400.0 AS days_since,
                  (SELECT count(*) FROM interactions i WHERE i.contact_id = c.id AND i.occurred_at > now() - interval '90 days') AS freq90,
                  (SELECT count(*) FROM signals s WHERE s.contact_id = c.id AND s.status = 'open') AS open_signals
           FROM contacts c
           WHERE c.user_id = %s AND c.noise_status IN ('real', 'review') AND c.is_user_self = false""",
        (user_id,),
    )
    tier_weight = {1: 1.0, 2: 0.75, 3: 0.5}
    for r in rows:
        days = float(r["days_since"] if r["days_since"] is not None else 365)
        recency = math.exp(-max(days, 0) / 30.0)
        frequency = min(int(r["freq90"]) / 8.0, 1.0)
        tw = tier_weight[int(r["tier"])]
        base = 0.4 * recency + 0.3 * frequency + 0.3 * tw
        boost = min(int(r["open_signals"]), 3) * 0.15
        penalty = 0.3 if r["noise_status"] == "review" else 0.0
        score = round(max(0.0, min(1.0, base + boost - penalty)) * 100, 1)
        factors = {
            "recency": round(recency, 3),
            "frequency": round(frequency, 3),
            "tier_weight": tw,
            "signal_boost": round(boost, 3),
            "review_penalty": penalty,
            "days_since_last": round(days, 1),
        }
        db.execute(
            """INSERT INTO network_scores (user_id, contact_id, score, factors, model_version)
               VALUES (%s, %s, %s, %s, 'det-v0')""",
            (user_id, r["id"], score, db.jsonb(factors)),
        )
    return _merge(state, "scoring", {"scored": len(rows)})


# ---------------------------------------------------------------------------
# STAGE 6: EMBEDDINGS FOR REAL CONTENT
# ---------------------------------------------------------------------------

def embed_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    if not state.get("llm", True):
        return _merge(state, "embeddings", {"skipped": "llm disabled"})
    rows = db.q(
        """SELECT r.id, r.subject, r.body_text
           FROM raw_emails r
           JOIN envelope_observations eo ON eo.raw_email_id = r.id AND eo.final_verdict = 'real'
           LEFT JOIN embeddings e ON e.source_kind = 'raw_email' AND e.source_id = r.id
           WHERE r.user_id = %s AND e.id IS NULL
           LIMIT 20""",
        (user_id,),
    )
    if not rows:
        return _merge(state, "embeddings", {"embedded": 0})
    try:
        texts = [f"{r['subject']}\n{r['body_text'][:800]}" for r in rows]
        vectors = embed(texts, input_type="passage")
        for r, vec in zip(rows, vectors):
            db.execute(
                """INSERT INTO embeddings (user_id, source_kind, source_id, content_preview, embedding)
                   VALUES (%s, 'raw_email', %s, %s, %s::vector) ON CONFLICT DO NOTHING""",
                (user_id, r["id"], texts[0][:200] if r is rows[0] else f"{r['subject']}"[:200], json.dumps(vec)),
            )
        return _merge(state, "embeddings", {"embedded": len(rows)})
    except LLMDisabled:
        return _merge(state, "embeddings", {"skipped": "llm disabled"})
    except Exception as exc:
        log.warning("embedding stage failed: %s", exc)
        return _merge(state, "embeddings", {"error": str(exc)[:200]})


# ---------------------------------------------------------------------------
# STAGE 7: MORNING BRIEF
# ---------------------------------------------------------------------------

def _brief_data(user_id: str) -> dict:
    contacts = db.q(
        """SELECT c.id, c.display_name, c.company, c.title, c.tier, ns.score,
                  c.last_interaction_at
           FROM contacts c
           JOIN LATERAL (
             SELECT score FROM network_scores WHERE contact_id = c.id ORDER BY computed_at DESC LIMIT 1
           ) ns ON true
           WHERE c.user_id = %s AND c.noise_status = 'real' AND c.is_user_self = false
           ORDER BY ns.score DESC LIMIT 8""",
        (user_id,),
    )
    out = []
    for c in contacts:
        signals = db.q(
            "SELECT id, type, evidence, detected_at FROM signals WHERE contact_id = %s AND status = 'open'",
            (c["id"],),
        )
        recent = db.q(
            """SELECT kind, occurred_at, snippet, source_table, source_id
               FROM interactions WHERE contact_id = %s ORDER BY occurred_at DESC LIMIT 3""",
            (c["id"],),
        )
        out.append(
            {
                "contact_id": str(c["id"]),
                "name": c["display_name"],
                "company": c["company"],
                "title": c["title"],
                "tier": c["tier"],
                "score": float(c["score"]),
                "open_signals": [
                    {"id": f"signal:{s['id']}", "type": s["type"], "evidence": s["evidence"]} for s in signals
                ],
                "recent": [
                    {
                        "kind": r["kind"],
                        "at": str(r["occurred_at"]),
                        "snippet": r["snippet"],
                        "cite": f"{'raw_email' if r['source_table'] == 'raw_emails' else 'calendar_event'}:{r['source_id']}",
                    }
                    for r in recent
                ],
            }
        )
    return {"contacts": out}


def brief_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    if not state.get("llm", True):
        return _merge(state, "brief", {"skipped": "llm disabled"})
    data = _brief_data(user_id)
    if not data["contacts"]:
        return _merge(state, "brief", {"skipped": "no real contacts"})
    memories = memory.recall(user_id, "communication and outreach preferences")
    today = date.today().isoformat()
    try:
        result = chat_json(
            prompts.BRIEF_SYSTEM,
            prompts.brief_user(today, data, memories),
            think=False,  # think mode made generations so slow the nvidia gateway 504'd
            temperature=0.6,
            max_tokens=4000,
        )
        db.execute(
            """INSERT INTO briefs (user_id, brief_date, content_md, items, model_version)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (user_id, brief_date) DO UPDATE SET
                 content_md = EXCLUDED.content_md, items = EXCLUDED.items,
                 model_version = EXCLUDED.model_version, created_at = now()""",
            (user_id, today, result.get("content_md", ""), db.jsonb(result.get("items", [])), settings.chat_model),
        )
        return _merge(state, "brief", {"generated": True, "items": len(result.get("items", []))})
    except LLMDisabled:
        return _merge(state, "brief", {"skipped": "llm disabled"})
    except Exception as exc:
        log.warning("brief stage failed: %s", exc)
        return _merge(state, "brief", {"error": str(exc)[:200]})


# ---------------------------------------------------------------------------
# STAGE 8: OUTREACH DRAFTS
# ---------------------------------------------------------------------------

DEFAULT_VOICE = {"tone": "warm and direct", "length": "short", "formality": "casual professional", "signoff": "first name"}


def draft_node(state: PipelineState) -> dict:
    user_id = state["user_id"]
    if not state.get("llm", True):
        return _merge(state, "drafts", {"skipped": "llm disabled"})
    rows = db.q(
        """SELECT DISTINCT ON (c.id) c.id AS contact_id, c.display_name, c.company, c.title,
                  s.id AS signal_id, s.type, s.evidence, ns.score
           FROM signals s
           JOIN contacts c ON c.id = s.contact_id
           JOIN LATERAL (
             SELECT score FROM network_scores WHERE contact_id = c.id ORDER BY computed_at DESC LIMIT 1
           ) ns ON true
           WHERE s.user_id = %s AND s.status = 'open' AND c.noise_status = 'real'
             AND NOT EXISTS (SELECT 1 FROM drafts d WHERE d.contact_id = c.id AND d.status = 'pending')
           ORDER BY c.id, ns.score DESC""",
        (user_id,),
    )
    rows = sorted(rows, key=lambda r: -float(r["score"]))[:DRAFT_LIMIT]
    voice_row = db.q1("SELECT traits FROM voice_profiles WHERE user_id = %s", (user_id,))
    voice = voice_row["traits"] if voice_row else DEFAULT_VOICE
    made = 0
    for r in rows:
        thread = db.q(
            """SELECT kind, occurred_at, snippet, source_table, source_id
               FROM interactions WHERE contact_id = %s ORDER BY occurred_at DESC LIMIT 4""",
            (r["contact_id"],),
        )
        thread_data = [
            {"kind": t["kind"], "at": str(t["occurred_at"]), "snippet": t["snippet"], "cite": f"{t['source_table']}:{t['source_id']}"}
            for t in thread
        ]
        contact = {"name": r["display_name"], "company": r["company"], "title": r["title"]}
        signal = {"id": f"signal:{r['signal_id']}", "type": r["type"], "evidence": r["evidence"]}
        memories = memory.recall(user_id, f"feedback on drafts and how the user writes to {r['display_name']}")
        try:
            result = chat_json(
                prompts.DRAFT_SYSTEM,
                prompts.draft_user(contact, signal, thread_data, voice, memories),
                temperature=0.7,
                max_tokens=1200,
            )
            db.execute(
                """INSERT INTO drafts (user_id, contact_id, signal_id, subject, body_text, rationale, citations, model_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    user_id,
                    r["contact_id"],
                    r["signal_id"],
                    str(result.get("subject", ""))[:300],
                    str(result.get("body_text", "")),
                    str(result.get("rationale", ""))[:500],
                    db.jsonb(result.get("citations", [])),
                    settings.chat_model,
                ),
            )
            made += 1
        except LLMDisabled:
            return _merge(state, "drafts", {"skipped": "llm disabled", "created": made})
        except Exception as exc:
            log.warning("draft stage failed for contact %s: %s", r["contact_id"], exc)
    return _merge(state, "drafts", {"created": made})


# ---------------------------------------------------------------------------
# GRAPH ASSEMBLY AND RUNNER
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("envelope_rules", envelope_rules_node)
    g.add_node("llm_triage", llm_triage_node)
    g.add_node("identity", identity_node)
    g.add_node("signals", signal_node)
    g.add_node("scoring", scoring_node)
    g.add_node("embeddings", embed_node)
    g.add_node("brief", brief_node)
    g.add_node("drafts", draft_node)
    g.add_edge(START, "envelope_rules")
    g.add_edge("envelope_rules", "llm_triage")
    g.add_edge("llm_triage", "identity")
    g.add_edge("identity", "signals")
    g.add_edge("signals", "scoring")
    g.add_edge("scoring", "embeddings")
    g.add_edge("embeddings", "brief")
    g.add_edge("brief", "drafts")
    g.add_edge("drafts", END)
    return g.compile()


GRAPH = build_graph()


def run_pipeline(user_id: str, trigger: str = "api", llm: bool | None = None) -> dict:
    """Run the full pipeline for one user. Returns per-stage stats."""
    use_llm = settings.llm_enabled if llm is None else llm
    run = db.q1(
        "INSERT INTO pipeline_runs (user_id, trigger) VALUES (%s, %s) RETURNING id",
        (user_id, trigger),
    )
    run_id = str(run["id"])
    state: PipelineState = {"user_id": str(user_id), "run_id": run_id, "llm": use_llm, "stats": {}}
    try:
        final = GRAPH.invoke(state)
        stats = final.get("stats", {})
        db.execute(
            "UPDATE pipeline_runs SET status = 'ok', stage_stats = %s, finished_at = now() WHERE id = %s",
            (db.jsonb(stats), run_id),
        )
        cache.invalidate(f"andi:{user_id}:*")
        return {"run_id": run_id, "status": "ok", "stats": stats}
    except Exception as exc:
        db.execute(
            "UPDATE pipeline_runs SET status = 'failed', error = %s, finished_at = now() WHERE id = %s",
            (str(exc)[:1000], run_id),
        )
        raise
