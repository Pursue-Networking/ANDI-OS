"""Shared FastAPI dependencies: auth stub and default user resolution."""

from fastapi import Header, HTTPException

from .. import db
from ..config import settings


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Dummy auth: one shared key in the X-API-Key header."""
    if x_api_key != settings.backend_api_key:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key header")


def default_user_id() -> str:
    """Single-user prototype: every request acts as the first seeded user."""
    row = db.q1("SELECT id FROM users ORDER BY created_at LIMIT 1")
    if not row:
        raise HTTPException(status_code=500, detail="no user in database, apply seed.sql first")
    return str(row["id"])
