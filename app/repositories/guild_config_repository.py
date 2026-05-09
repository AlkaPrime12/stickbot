import sqlite3

from app.db import get_connection
from app.guild_config_defaults import default_guild_config_dict


class GuildConfigRepository:
    def get(self, guild_id: str) -> dict | None:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?",
                (str(guild_id),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def upsert(self, guild_id: str, payload: dict) -> None:
        base = default_guild_config_dict(str(guild_id))
        merged = {**base, **payload}
        merged["guild_id"] = str(guild_id)

        with get_connection() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(guild_config)").fetchall()]
            values = []
            for col in cols:
                if col not in merged:
                    values.append(base.get(col))
                else:
                    values.append(merged[col])
            placeholders = ",".join(["?"] * len(cols))
            col_list = ",".join(cols)
            sql = f"INSERT OR REPLACE INTO guild_config ({col_list}) VALUES ({placeholders})"
            conn.execute(sql, values)
