from app.db import get_connection


class GuildConfigRepository:
    def get(self, guild_id: str):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT guild_id, channel_buzon_id, channel_registro_id, channel_historial_id,
                       channel_general_id, channel_busqueda_id, role_buscando_id,
                       cooldown_minutes, daily_limit, auto_mode
                FROM guild_config
                WHERE guild_id = ?
                """,
                (guild_id,),
            ).fetchone()

    def upsert(self, guild_id: str, payload: dict):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO guild_config (
                    guild_id, channel_buzon_id, channel_registro_id, channel_historial_id,
                    channel_general_id, channel_busqueda_id, role_buscando_id,
                    cooldown_minutes, daily_limit, auto_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_buzon_id=excluded.channel_buzon_id,
                    channel_registro_id=excluded.channel_registro_id,
                    channel_historial_id=excluded.channel_historial_id,
                    channel_general_id=excluded.channel_general_id,
                    channel_busqueda_id=excluded.channel_busqueda_id,
                    role_buscando_id=excluded.role_buscando_id,
                    cooldown_minutes=excluded.cooldown_minutes,
                    daily_limit=excluded.daily_limit,
                    auto_mode=excluded.auto_mode
                """,
                (
                    guild_id,
                    payload.get("channel_buzon_id"),
                    payload.get("channel_registro_id"),
                    payload.get("channel_historial_id"),
                    payload.get("channel_general_id"),
                    payload.get("channel_busqueda_id"),
                    payload.get("role_buscando_id"),
                    payload.get("cooldown_minutes"),
                    payload.get("daily_limit"),
                    payload.get("auto_mode", 0),
                ),
            )
