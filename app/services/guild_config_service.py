from app.guild_config_defaults import default_guild_config_dict
from app.repositories.guild_config_repository import GuildConfigRepository


class GuildConfigService:
    def __init__(self):
        self.repo = GuildConfigRepository()

    def get_or_default(self, guild_id: str) -> dict:
        base = default_guild_config_dict(str(guild_id))
        row = self.repo.get(guild_id)
        if row:
            for k in base:
                if k in row:
                    base[k] = row[k]
        return base

    def save(self, guild_id: str, payload: dict) -> dict:
        current = self.get_or_default(guild_id)
        current.update(payload)
        self.repo.upsert(guild_id, current)
        return self.get_or_default(guild_id)
