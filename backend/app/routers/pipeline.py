"""Run and inspect the LangGraph pipeline."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db
from ..agents.graph import run_pipeline
from .deps import default_user_id

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class RunRequest(BaseModel):
    llm: bool | None = None  # None = use LLM_ENABLED from settings
    trigger: str = "api"


@router.post("/run")
def run(body: RunRequest | None = None, user_id: str = Depends(default_user_id)):
    body = body or RunRequest()
    try:
        return run_pipeline(user_id, trigger=body.trigger, llm=body.llm)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pipeline failed: {exc}") from exc


@router.get("/runs")
def runs(user_id: str = Depends(default_user_id)):
    return db.q(
        """SELECT id, trigger, status, stage_stats, error, started_at, finished_at
           FROM pipeline_runs WHERE user_id = %s ORDER BY started_at DESC LIMIT 20""",
        (user_id,),
    )
