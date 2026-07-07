"""Mem0 hosted memory. Fail-open by design: memory should never break the API.

Scoping: mem0 user_id = str(our users.id uuid). Every memory we create is also
linked locally in the memory_refs table so rows stay auditable.
"""

import logging

from .config import settings
from . import db

log = logging.getLogger(__name__)

_mc = None


def mclient():
    global _mc
    if not settings.mem0_api_key:
        return None
    if _mc is None:
        try:
            from mem0 import MemoryClient

            _mc = MemoryClient(api_key=settings.mem0_api_key)
        except Exception as exc:
            log.warning("mem0 client init failed: %s", exc)
            return None
    return _mc


def remember(user_id, text: str, kind: str = "fact", contact_id=None, metadata: dict | None = None) -> str | None:
    """Store one memory in Mem0 and link it in memory_refs. Returns mem id or None."""
    mc = mclient()
    if mc is None:
        return None
    try:
        result = mc.add(
            [{"role": "user", "content": text}],
            user_id=str(user_id),
            metadata={"kind": kind, **(metadata or {})},
        )
        mem_id = ""
        if isinstance(result, dict):
            items = result.get("results") or []
            if items and isinstance(items[0], dict):
                mem_id = str(items[0].get("id", ""))
        db.execute(
            "INSERT INTO memory_refs (user_id, contact_id, mem_id, kind, note) VALUES (%s, %s, %s, %s, %s)",
            (user_id, contact_id, mem_id or "pending", kind, text[:500]),
        )
        return mem_id or None
    except Exception as exc:
        log.warning("mem0 remember failed: %s", exc)
        return None


def recall(user_id, query: str, limit: int = 5) -> list[str]:
    """Search memories for this user. Returns plain memory strings."""
    mc = mclient()
    if mc is None:
        return []
    try:
        # this mem0 SDK version rejects top-level user_id in search(); it wants filters=
        result = mc.search(query, filters={"user_id": str(user_id)}, limit=limit)
        items = result.get("results", result) if isinstance(result, dict) else result
        memories = []
        for item in items or []:
            if isinstance(item, dict) and item.get("memory"):
                memories.append(str(item["memory"]))
        return memories[:limit]
    except Exception as exc:
        log.warning("mem0 recall failed: %s", exc)
        return []
