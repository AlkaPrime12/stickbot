"""
Smoke tests opcionales contra Postgres cuando DATABASE_URL está definido (ej. CI).
Sin DATABASE_URL estos tests no se ejecutan para no pegar SQLite en modo multi-proceso.
"""
from __future__ import annotations

import os

import pytest

from app.config import uses_postgresql


pytestmark = pytest.mark.skipif(
    not uses_postgresql(),
    reason="Define DATABASE_URL para habilitar smoke Postgres.",
)


@pytest.fixture(scope="module", autouse=True)
def _ensure_pg_schema():
    from app.runtime_migrate import ensure_schema

    ensure_schema()


def test_health_query_runs():
    from app.db import get_connection

    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM jugadores", {}).fetchone()
        assert row is not None
        assert int(row._mapping["c"]) >= 0


def test_guild_config_upsert_roundtrip():
    from app.repositories.guild_config_repository import GuildConfigRepository

    repo = GuildConfigRepository()
    gid = "__smoke_ci_guild__"
    repo.upsert(
        gid,
        {
            "guild_display_name": "CI Smoke Guild",
            "daily_limit": 3,
            "cooldown_minutes": 22,
        },
    )
    row = repo.get(gid)
    assert row is not None
    assert row.get("guild_display_name") == "CI Smoke Guild"
