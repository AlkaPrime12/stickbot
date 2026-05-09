"""
Conexiones transaccionales vía SQLAlchemy 2.
Usar SQL con placeholders **:nombre** y dict de parámetros (portable Postgres + SQLite).

Ver docs internos en docs/sql_style.md
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Connection, CursorResult

from app.database_engine import engine


class ConnWrapper:
    """Adaptador mínimo para `text()` + parámetros nombrados."""

    __slots__ = ("_c",)

    def __init__(self, conn: Connection):
        self._c = conn

    def execute(
        self,
        sql: str | Any,
        params: Mapping[str, Any] | None = None,
    ) -> CursorResult[Any]:
        stmt = text(sql) if isinstance(sql, str) else sql
        return self._c.execute(stmt, dict(params or {}))


@contextmanager
def get_connection():
    conn = engine.connect()
    trans = conn.begin()
    try:
        yield ConnWrapper(conn)
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
