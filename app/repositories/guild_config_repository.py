from __future__ import annotations

from app.db import get_connection
from app.guild_config_columns import GUILD_CONFIG_COLUMNS
from app.guild_config_defaults import default_guild_config_dict


def _upsert_sql() -> str:
    cols = list(GUILD_CONFIG_COLUMNS)
    ph = ", ".join(f":{c}" for c in cols)
    col_list = ", ".join(cols)
    # EXCLUDED síncrono Postgres + SQLite
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "guild_id")
    return f"""
INSERT INTO guild_config ({col_list})
VALUES ({ph})
ON CONFLICT (guild_id) DO UPDATE SET {updates}
"""


_UPSERT_SQL = _upsert_sql()


class GuildConfigRepository:
    def get(self, guild_id: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM guild_config WHERE guild_id = :gid",
                {"gid": str(guild_id)},
            ).fetchone()
            if not row:
                return None
            return dict(row._mapping)

    def upsert(self, guild_id: str, payload: dict) -> None:
        base = default_guild_config_dict(str(guild_id))
        merged = {**base, **payload}
        merged["guild_id"] = str(guild_id)
        params: dict = {}
        for c in GUILD_CONFIG_COLUMNS:
            val = merged.get(c, base.get(c))
            params[c] = val
        with get_connection() as conn:
            conn.execute(_UPSERT_SQL, params)
