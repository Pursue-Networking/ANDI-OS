"""Redis caching. Fail-open: if redis is down, every call falls back to the
producer function so the API keeps working, just slower.
"""

import json
import logging

import redis

from .config import settings

log = logging.getLogger(__name__)

_r = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)


def ping() -> bool:
    try:
        return bool(_r.ping())
    except Exception:
        return False


def cached_json(key: str, ttl_seconds: int, producer):
    """Return cached value for key, or run producer, cache it, return it."""
    try:
        hit = _r.get(key)
        if hit is not None:
            return json.loads(hit)
    except Exception as exc:
        log.warning("redis get failed for %s: %s", key, exc)
    value = producer()
    try:
        _r.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception as exc:
        log.warning("redis set failed for %s: %s", key, exc)
    return value


def invalidate(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns count deleted."""
    try:
        keys = list(_r.scan_iter(pattern))
        if keys:
            _r.delete(*keys)
        return len(keys)
    except Exception as exc:
        log.warning("redis invalidate failed for %s: %s", pattern, exc)
        return 0
