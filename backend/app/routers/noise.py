"""Noise system endpoints: review queue, stats, and human labels.

Human labels are the highest authority. They update the observation or the
contact, land in noise_labels as training data, and are pushed to Mem0 so
future runs remember the preference.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import cache, db, memory
from .deps import default_user_id

router = APIRouter(prefix="/noise", tags=["noise"])


@router.get("/review")
def review_queue(user_id: str = Depends(default_user_id)):
    contacts = db.q(
        """SELECT id AS contact_id, display_name, primary_email, noise_score, noise_reasons, last_interaction_at
           FROM contacts WHERE user_id = %s AND noise_status = 'review'
           ORDER BY last_interaction_at DESC NULLS LAST""",
        (user_id,),
    )
    observations = db.q(
        """SELECT eo.id AS observation_id, eo.raw_email_id, eo.sender_email, eo.rule_score,
                  eo.rule_verdict, eo.llm_verdict, eo.llm_confidence, eo.llm_reason, eo.features,
                  r.subject, r.snippet, r.internal_date
           FROM envelope_observations eo
           JOIN raw_emails r ON r.id = eo.raw_email_id
           WHERE eo.user_id = %s AND eo.final_verdict = 'uncertain'
           ORDER BY r.internal_date DESC""",
        (user_id,),
    )
    return {"contacts": contacts, "observations": observations}


@router.get("/stats")
def stats(user_id: str = Depends(default_user_id)):
    verdicts = db.q(
        """SELECT final_verdict, decided_by, count(*) AS n
           FROM envelope_observations WHERE user_id = %s
           GROUP BY final_verdict, decided_by ORDER BY n DESC""",
        (user_id,),
    )
    totals = db.q1(
        """SELECT
             (SELECT count(*) FROM raw_emails WHERE user_id = %s AND direction = 'inbound') AS inbound_emails,
             (SELECT count(*) FROM envelope_observations WHERE user_id = %s) AS observations,
             (SELECT count(*) FROM envelope_observations WHERE user_id = %s AND final_verdict = 'noise') AS noise,
             (SELECT count(*) FROM noise_labels WHERE user_id = %s) AS human_labels""",
        (user_id, user_id, user_id, user_id),
    )
    return {"verdicts": verdicts, "totals": totals}


class LabelIn(BaseModel):
    label: str  # real | noise
    contact_id: str | None = None
    raw_email_id: str | None = None
    note: str = ""


@router.post("/label")
def label(body: LabelIn, user_id: str = Depends(default_user_id)):
    if body.label not in ("real", "noise"):
        raise HTTPException(status_code=422, detail="label must be real or noise")
    if not body.contact_id and not body.raw_email_id:
        raise HTTPException(status_code=422, detail="provide contact_id or raw_email_id")

    labeled = ""
    if body.raw_email_id:
        obs = db.q1(
            "SELECT id, sender_email FROM envelope_observations WHERE raw_email_id = %s AND user_id = %s",
            (body.raw_email_id, user_id),
        )
        if not obs:
            raise HTTPException(status_code=404, detail="no observation for that raw_email_id")
        db.execute(
            "UPDATE envelope_observations SET final_verdict = %s, decided_by = 'human' WHERE id = %s",
            (body.label, obs["id"]),
        )
        labeled = obs["sender_email"]

    if body.contact_id:
        contact = db.q1(
            "SELECT id, display_name, primary_email FROM contacts WHERE id = %s AND user_id = %s",
            (body.contact_id, user_id),
        )
        if not contact:
            raise HTTPException(status_code=404, detail="contact not found")
        db.execute(
            """UPDATE contacts SET noise_status = %s,
                 noise_score = %s,
                 noise_reasons = noise_reasons || %s::jsonb,
                 updated_at = now()
               WHERE id = %s""",
            (body.label, 0.0 if body.label == "real" else 1.0, db.jsonb([f"human:{body.label}"]), body.contact_id),
        )
        labeled = contact["primary_email"]

    db.execute(
        """INSERT INTO noise_labels (user_id, contact_id, raw_email_id, label, source, note)
           VALUES (%s, %s, %s, %s, 'human', %s)""",
        (user_id, body.contact_id, body.raw_email_id, body.label, body.note),
    )
    db.execute(
        """INSERT INTO feedback_events (user_id, subject_kind, subject_id, action, detail)
           VALUES (%s, 'noise', %s, %s, %s)""",
        (user_id, body.contact_id or body.raw_email_id, f"labeled_{body.label}", db.jsonb({"note": body.note, "sender": labeled})),
    )
    memory.remember(
        user_id,
        f"The user marked sender {labeled} as {body.label}." + (f" Note: {body.note}" if body.note else ""),
        kind="feedback",
        contact_id=body.contact_id,
    )
    cache.invalidate(f"andi:{user_id}:*")
    return {"ok": True, "labeled": labeled, "label": body.label}
