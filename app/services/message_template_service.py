from app.message_defaults import MESSAGE_TEMPLATE_KEYS
from app.repositories.message_template_repository import MessageTemplateRepository


class MessageTemplateService:
    def __init__(self):
        self.repo = MessageTemplateRepository()

    def render(self, guild_id: str, key: str, **kwargs) -> str:
        custom = self.repo.get(str(guild_id), key) if guild_id else None
        raw = (
            custom.strip()
            if custom and str(custom).strip()
            else MESSAGE_TEMPLATE_KEYS.get(key, "")
        )
        if not raw:
            return key
        try:
            return raw.format(**kwargs)
        except Exception:
            return raw

    def get_all_merged(self, guild_id: str) -> dict[str, str]:
        defaults = dict(MESSAGE_TEMPLATE_KEYS)
        overrides = self.repo.get_all_for_guild(str(guild_id))
        defaults.update(overrides)
        return defaults

    def save_partial(self, guild_id: str, payload: dict[str, str]) -> None:
        clean = {k: (v or "")[:1900] for k, v in payload.items() if k in MESSAGE_TEMPLATE_KEYS}
        self.repo.upsert_many(guild_id, clean)
