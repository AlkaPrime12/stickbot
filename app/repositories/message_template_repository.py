import sqlite3

from app.db import get_connection


class MessageTemplateRepository:
    def get(self, guild_id: str, template_key: str) -> str | None:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT body FROM guild_message_templates
                WHERE guild_id = ? AND template_key = ?
                """,
                (str(guild_id), template_key),
            ).fetchone()
            if not row:
                return None
            return str(row["body"])

    def get_all_for_guild(self, guild_id: str) -> dict[str, str]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT template_key, body FROM guild_message_templates WHERE guild_id = ?",
                (str(guild_id),),
            ).fetchall()
            return {r[0]: r[1] for r in rows}

    def upsert_many(self, guild_id: str, templates: dict[str, str]) -> None:
        gid = str(guild_id)
        with get_connection() as conn:
            for key, body in templates.items():
                key = str(key).strip()
                if not key or len(str(body)) > 1900:
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO guild_message_templates (guild_id, template_key, body)
                    VALUES (?, ?, ?)
                    """,
                    (gid, key, str(body)[:1900]),
                )
