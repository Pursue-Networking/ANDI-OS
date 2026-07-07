"""Ranked contacts and per-contact dossier."""

from fastapi import APIRouter, Depends, HTTPException

from .. import cache, db, memory
from ..agents import prompts
from ..config import settings
from ..llm import LLMDisabled, chat_json
from .deps import default_user_id

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("")
def list_contacts(status: str = "real", limit: int = 50, user_id: str = Depends(default_user_id)):
    if status not in ("real", "review", "noise", "all"):
        raise HTTPException(status_code=422, detail="status must be real, review, noise or all")
    limit = max(1, min(limit, 200))

    def produce():
        status_sql = "" if status == "all" else "AND c.noise_status = %(status)s"
        return db.q(
            f"""SELECT c.id, c.display_name, c.primary_email, c.company, c.title, c.tier,
                       c.noise_status, c.noise_score, c.last_interaction_at,
                       ns.score, ns.factors,
                       (SELECT count(*) FROM signals s WHERE s.contact_id = c.id AND s.status = 'open') AS open_signals
                FROM contacts c
                LEFT JOIN LATERAL (
                  SELECT score, factors FROM network_scores
                  WHERE contact_id = c.id ORDER BY computed_at DESC LIMIT 1
                ) ns ON true
                WHERE c.user_id = %(user_id)s AND c.is_user_self = false {status_sql}
                ORDER BY ns.score DESC NULLS LAST, c.last_interaction_at DESC NULLS LAST
                LIMIT %(limit)s""",
            {"user_id": user_id, "status": status, "limit": limit},
        )

    return cache.cached_json(f"andi:{user_id}:contacts:{status}:{limit}", 60, produce)


@router.get("/{contact_id}")
def get_contact(contact_id: str, user_id: str = Depends(default_user_id)):
    contact = db.q1("SELECT * FROM contacts WHERE id = %s AND user_id = %s", (contact_id, user_id))
    if not contact:
        raise HTTPException(status_code=404, detail="contact not found")
    score = db.q1(
        "SELECT score, factors, computed_at FROM network_scores WHERE contact_id = %s ORDER BY computed_at DESC LIMIT 1",
        (contact_id,),
    )
    interactions = db.q(
        "SELECT kind, occurred_at, snippet, source_table, source_id FROM interactions WHERE contact_id = %s ORDER BY occurred_at DESC LIMIT 20",
        (contact_id,),
    )
    signals = db.q(
        "SELECT id, type, status, evidence, detected_at FROM signals WHERE contact_id = %s ORDER BY detected_at DESC",
        (contact_id,),
    )
    dossier = db.q1(
        "SELECT content_md, citations, model_version, generated_at FROM dossiers WHERE contact_id = %s",
        (contact_id,),
    )
    return {"contact": contact, "score": score, "interactions": interactions, "signals": signals, "dossier": dossier}


@router.post("/{contact_id}/dossier")
def generate_dossier(contact_id: str, user_id: str = Depends(default_user_id)):
    contact = db.q1(
        "SELECT id, display_name, primary_email, company, title, tier, first_seen_at, last_interaction_at FROM contacts WHERE id = %s AND user_id = %s",
        (contact_id, user_id),
    )
    if not contact:
        raise HTTPException(status_code=404, detail="contact not found")
    interactions = db.q(
        """SELECT kind, occurred_at, snippet,
                  source_table || ':' || source_id AS cite
           FROM interactions WHERE contact_id = %s ORDER BY occurred_at DESC LIMIT 25""",
        (contact_id,),
    )
    signals = db.q(
        "SELECT 'signal:' || id AS cite, type, evidence FROM signals WHERE contact_id = %s AND status = 'open'",
        (contact_id,),
    )
    memories = memory.recall(user_id, f"facts about {contact['display_name']}")
    try:
        result = chat_json(
            prompts.DOSSIER_SYSTEM,
            prompts.dossier_user(contact, interactions, signals, memories),
            think=True,
            temperature=0.4,
            max_tokens=2500,
        )
    except LLMDisabled as exc:
        raise HTTPException(status_code=503, detail=f"llm not available: {exc}") from exc
    db.execute(
        """INSERT INTO dossiers (user_id, contact_id, content_md, citations, model_version)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (contact_id) DO UPDATE SET
             content_md = EXCLUDED.content_md, citations = EXCLUDED.citations,
             model_version = EXCLUDED.model_version, generated_at = now()""",
        (user_id, contact_id, result.get("content_md", ""), db.jsonb(result.get("citations", [])), settings.chat_model),
    )
    cache.invalidate(f"andi:{user_id}:*")
    return {"contact_id": contact_id, "content_md": result.get("content_md", ""), "citations": result.get("citations", [])}
