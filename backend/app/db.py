"""psycopg3 connection pool plus tiny query helpers.

Every helper checks out a pooled connection and commits on clean exit.
Rows come back as plain dicts.
"""

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from .config import settings

pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={"row_factory": dict_row},
)

_opened = False


def ensure_open() -> None:
    global _opened
    if not _opened:
        pool.open()
        _opened = True


def close() -> None:
    """Close the pool (call at CLI exit to avoid noisy thread-shutdown warnings)."""
    global _opened
    if _opened:
        pool.close()
        _opened = False


def q(sql: str, params=None) -> list[dict]:
    """Run a query, return all rows as dicts."""
    ensure_open()
    with pool.connection() as conn:
        cur = conn.execute(sql, params)
        if cur.description is None:
            return []
        return cur.fetchall()


def q1(sql: str, params=None) -> dict | None:
    """Run a query, return the first row or None."""
    rows = q(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None) -> int:
    """Run a statement, return affected row count."""
    ensure_open()
    with pool.connection() as conn:
        cur = conn.execute(sql, params)
        return cur.rowcount


def jsonb(value) -> Jsonb:
    """Wrap a python object for a jsonb column."""
    return Jsonb(value)
