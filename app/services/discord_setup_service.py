import httpx
from app.config import settings


class DiscordSetupService:
    API = "https://discord.com/api/v10"

    def __init__(self):
        self.bot_headers = {"Authorization": f"Bot {settings.discord_token}"}

    async def create_text_channel(self, guild_id: str, name: str, category_id: str | None = None):
        payload = {"name": name, "type": 0}
        if category_id:
            payload["parent_id"] = category_id
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.API}/guilds/{guild_id}/channels", headers=self.bot_headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def create_category(self, guild_id: str, name: str):
        payload = {"name": name, "type": 4}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.API}/guilds/{guild_id}/channels", headers=self.bot_headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def create_role(self, guild_id: str, name: str):
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.API}/guilds/{guild_id}/roles", headers=self.bot_headers, json={"name": name})
            resp.raise_for_status()
            return resp.json()

    async def auto_setup(self, guild_id: str):
        report = {"created": [], "failed": []}
        category = await self.create_category(guild_id, "StickBot")
        report["created"].append(f"categoria:{category['id']}")

        channels = {}
        for key, name in [
            ("channel_registro_id", "stick-registro"),
            ("channel_buzon_id", "stick-buzon"),
            ("channel_historial_id", "stick-historial"),
            ("channel_general_id", "stick-general"),
            ("channel_busqueda_id", "stick-busqueda"),
        ]:
            try:
                ch = await self.create_text_channel(guild_id, name, category["id"])
                channels[key] = ch["id"]
                report["created"].append(f"canal:{name}:{ch['id']}")
            except Exception as exc:  # noqa: BLE001
                report["failed"].append(f"canal:{name}:{exc}")

        role_id = None
        try:
            role = await self.create_role(guild_id, "Buscando Partida")
            role_id = role["id"]
            report["created"].append(f"rol:{role_id}")
        except Exception as exc:  # noqa: BLE001
            report["failed"].append(f"rol:{exc}")

        return channels, role_id, report
