from app.config import settings
from app.repositories.guild_config_repository import GuildConfigRepository


class GuildConfigService:
    def __init__(self):
        self.repo = GuildConfigRepository()

    def get_or_default(self, guild_id: str):
        row = self.repo.get(guild_id)
        if row:
            return {
                "guild_id": row[0],
                "channel_buzon_id": row[1],
                "channel_registro_id": row[2],
                "channel_historial_id": row[3],
                "channel_general_id": row[4],
                "channel_busqueda_id": row[5],
                "role_buscando_id": row[6],
                "cooldown_minutes": row[7],
                "daily_limit": row[8],
                "auto_mode": row[9],
            }
        return {
            "guild_id": guild_id,
            "channel_buzon_id": None,
            "channel_registro_id": None,
            "channel_historial_id": None,
            "channel_general_id": None,
            "channel_busqueda_id": None,
            "role_buscando_id": None,
            "cooldown_minutes": settings.default_cooldown_minutes,
            "daily_limit": settings.default_daily_limit,
            "auto_mode": 0,
        }

    def save(self, guild_id: str, payload: dict):
        base = self.get_or_default(guild_id)
        base.update(payload)
        self.repo.upsert(guild_id, base)
        return base
