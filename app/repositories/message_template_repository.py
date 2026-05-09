from __future__ import annotations

from app.db import get_connection


_MT_UPSERT = """
INSERT INTO guild_message_templates (guild_id, template_key, body)
VALUES (:guild_id, :template_key, :body)
ON CONFLICT (guild_id, template_key) DO UPDATE SET body = EXCLUDED.body
"""


class MessageTemplateRepository:
    def get(self, guild_id: str, template_key: str) -> str | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT body FROM guild_message_templates
                WHERE guild_id = :guild_id AND template_key = :template_key
                """,
                {"guild_id": str(guild_id), "template_key": template_key},
            ).fetchone()
            if not row:
                return None
            return str(row._mapping["body"])

    def get_all_for_guild(self, guild_id: str) -> dict[str, str]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT template_key, body FROM guild_message_templates WHERE guild_id = :gid",
                {"gid": str(guild_id)},
            ).fetchall()
            return {r._mapping["template_key"]: r._mapping["body"] for r in rows}

    def upsert_many(self, guild_id: str, templates: dict[str, str]) -> None:
        gid = str(guild_id)
        with get_connection() as conn:
            for key, body in templates.items():
                key = str(key).strip()
                if not key or len(str(body)) > 1900:
                    continue
                conn.execute(
                    _MT_UPSERT,
                    {"guild_id": gid, "template_key": key, "body": str(body)[:1900]},
                )
