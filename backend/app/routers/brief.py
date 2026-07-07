"""Morning brief endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from .. import cache, db
from .deps import default_user_id

router = APIRouter(prefix="/brief", tags=["brief"])


@router.get("/today")
def today(user_id: str = Depends(default_user_id)):
    def produce():
        row = db.q1(
            "SELECT id, brief_date, content_md, items, model_version, created_at FROM briefs WHERE user_id = %s AND brief_date = current_date",
            (user_id,),
        )
        return row or {}

    row = cache.cached_json(f"andi:{user_id}:brief:today", 120, produce)
    if not row:
        raise HTTPException(status_code=404, detail="no brief for today yet, run POST /v1/pipeline/run first")
    return row


@router.get("/history")
def history(limit: int = 14, user_id: str = Depends(default_user_id)):
    return db.q(
        "SELECT id, brief_date, status, model_version, created_at FROM briefs WHERE user_id = %s ORDER BY brief_date DESC LIMIT %s",
        (user_id, max(1, min(limit, 60))),
    )
