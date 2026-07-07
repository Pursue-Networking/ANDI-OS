"""ANDI prototype backend. Run from the repo root:

    uvicorn backend.app.main:app --reload --port 8000

Every /v1 route needs the X-API-Key header (see BACKEND_API_KEY in .env).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import cache, db
from .config import settings
from .routers import brief, contacts, drafts, ingest, noise, pipeline
from .routers.deps import require_api_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.ensure_open()
    yield
    db.pool.close()


app = FastAPI(
    title="ANDI Backend",
    version="0.1.0",
    description="Prototype backend: gmail-shaped ingestion, noise detection, scoring, signals, brief, dossiers, drafts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    try:
        db.q1("SELECT 1 AS ok")
        db_ok = True
    except Exception:
        db_ok = False
    redis_ok = cache.ping()
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "db": db_ok,
        "redis": redis_ok,
        "llm_configured": bool(settings.nvidia_api_key) and settings.llm_enabled,
        "mem0_configured": bool(settings.mem0_api_key),
        "chat_model": settings.chat_model,
        "embed_model": settings.embed_model,
    }


secured = [Depends(require_api_key)]
app.include_router(ingest.router, prefix="/v1", dependencies=secured)
app.include_router(pipeline.router, prefix="/v1", dependencies=secured)
app.include_router(contacts.router, prefix="/v1", dependencies=secured)
app.include_router(noise.router, prefix="/v1", dependencies=secured)
app.include_router(brief.router, prefix="/v1", dependencies=secured)
app.include_router(drafts.router, prefix="/v1", dependencies=secured)
