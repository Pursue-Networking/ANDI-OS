"""Draft queue and human decisions. ANDI never sends email."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import cache, db, memory
from .deps import default_user_id

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("")
def list_drafts(status: str = "pending", user_id: str = Depends(default_user_id)):
    if status not in ("pending", "approved", "edited", "rejected", "sent", "all"):
        raise HTTPException(status_code=422, detail="bad status filter")
    status_sql = "" if status == "all" else "AND d.status = %(status)s"
    return db.q(
        f"""SELECT d.id, d.status, d.subject, d.body_text, d.rationale, d.citations,
                   d.user_feedback, d.created_at, d.decided_at,
                   c.id AS contact_id, c.display_name, c.primary_email,
                   s.type AS signal_type
            FROM drafts d
            JOIN contacts c ON c.id = d.contact_id
            LEFT JOIN signals s ON s.id = d.signal_id
            WHERE d.user_id = %(user_id)s {status_sql}
            ORDER BY d.created_at DESC LIMIT 50""",
        {"user_id": user_id, "status": status},
    )


class DecisionIn(BaseModel):
    action: str  # approve | reject | edit
    feedback: str = ""
    edited_body: str = ""


@router.post("/{draft_id}/decision")
def decide(draft_id: str, body: DecisionIn, user_id: str = Depends(default_user_id)):
    if body.action not in ("approve", "reject", "edit"):
        raise HTTPException(status_code=422, detail="action must be approve, reject or edit")
    draft = db.q1(
        """SELECT d.id, d.contact_id, d.signal_id, c.display_name
           FROM drafts d JOIN contacts c ON c.id = d.contact_id
           WHERE d.id = %s AND d.user_id = %s""",
        (draft_id, user_id),
    )
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    if body.action == "edit" and not body.edited_body:
        raise HTTPException(status_code=422, detail="edit needs edited_body")

    new_status = {"approve": "approved", "reject": "rejected", "edit": "edited"}[body.action]
    if body.action == "edit":
        db.execute(
            "UPDATE drafts SET status = %s, body_text = %s, user_feedback = %s, decided_at = now() WHERE id = %s",
            (new_status, body.edited_body, body.feedback, draft_id),
        )
    else:
        db.execute(
            "UPDATE drafts SET status = %s, user_feedback = %s, decided_at = now() WHERE id = %s",
            (new_status, body.feedback, draft_id),
        )
    if draft["signal_id"]:
        db.execute("UPDATE signals SET status = 'used' WHERE id = %s AND %s <> 'reject'", (draft["signal_id"], body.action))
    db.execute(
        """INSERT INTO feedback_events (user_id, subject_kind, subject_id, action, detail)
           VALUES (%s, 'draft', %s, %s, %s)""",
        (user_id, draft_id, new_status, db.jsonb({"feedback": body.feedback})),
    )
    memory.remember(
        user_id,
        f"The user {new_status} a draft to {draft['display_name']}." + (f" Feedback: {body.feedback}" if body.feedback else ""),
        kind="feedback",
        contact_id=draft["contact_id"],
    )
    cache.invalidate(f"andi:{user_id}:*")
    return db.q1("SELECT id, status, subject, body_text, user_feedback, decided_at FROM drafts WHERE id = %s", (draft_id,))
