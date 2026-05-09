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

    async def find_or_create_role(self, guild_id: str, name: str):
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.API}/guilds/{guild_id}/roles", headers=self.bot_headers)
            resp.raise_for_status()
            roles = resp.json()
        if isinstance(roles, list):
            for r in roles:
                if isinstance(r, dict) and (r.get("name") or "") == name:
                    return str(r["id"]), "reused"
        created = await self.create_role(guild_id, name)
        return str(created["id"]), "created"

    async def bot_in_guild(self, guild_id: str) -> bool:
        if not settings.discord_token:
            return False
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(f"{self.API}/guilds/{guild_id}", headers=self.bot_headers)
        return resp.status_code == 200

    async def list_guild_text_channels_raw(self, guild_id: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.API}/guilds/{guild_id}/channels", headers=self.bot_headers)
            resp.raise_for_status()
            data = resp.json()
        return data if isinstance(data, list) else []

    async def list_guild_text_channels(self, guild_id: str) -> list[dict]:
        """Canales de texto (type 0) para selectores del panel."""
        raw = await self.list_guild_text_channels_raw(guild_id)
        text = [ch for ch in raw if isinstance(ch, dict) and int(ch.get("type", -1)) == 0]
        text.sort(key=lambda ch: ((ch.get("parent_id") or ""), (ch.get("name") or "").lower()))
        return [
            {"id": str(ch["id"]), "name": ch.get("name") or "sin-nombre", "parent_id": ch.get("parent_id")}
            for ch in text
        ]

    def _pick_category_for_setup(self, all_channels: list[dict]):
        """Categoría type=4 llamada StickBot si existe."""
        for ch in all_channels:
            if isinstance(ch, dict) and int(ch.get("type", -1)) == 4:
                if (ch.get("name") or "").strip() == "StickBot":
                    return ch
        return None

    def _find_child_text_channel(self, all_channels: list[dict], parent_id: str, name: str) -> dict | None:
        for ch in all_channels:
            if not isinstance(ch, dict):
                continue
            if int(ch.get("type", -1)) != 0:
                continue
            if str(ch.get("parent_id") or "") != str(parent_id):
                continue
            if (ch.get("name") or "").strip() == name:
                return ch
        return None

    async def auto_setup(self, guild_id: str):
        report = {"created": [], "failed": [], "reused": []}
        all_before = await self.list_guild_text_channels_raw(guild_id)
        category_obj = self._pick_category_for_setup(all_before)

        try:
            if not category_obj:
                category_obj = await self.create_category(guild_id, "StickBot")
                report["created"].append(f"categoria:{category_obj['id']}")
            else:
                report["reused"].append(f"categoria:{category_obj['id']}:StickBot")

            category_id = str(category_obj["id"])
            all_live = await self.list_guild_text_channels_raw(guild_id)

            channels: dict[str, str] = {}
            for key, cname in [
                ("channel_registro_id", "stick-registro"),
                ("channel_buzon_id", "stick-buzon"),
                ("channel_historial_id", "stick-historial"),
                ("channel_general_id", "stick-general"),
                ("channel_busqueda_id", "stick-busqueda"),
            ]:
                found = self._find_child_text_channel(all_live, category_id, cname)
                if found:
                    channels[key] = str(found["id"])
                    report["reused"].append(f"canal:{cname}:{found['id']}")
                    continue
                try:
                    ch = await self.create_text_channel(guild_id, cname, category_id)
                    channels[key] = str(ch["id"])
                    report["created"].append(f"canal:{cname}:{ch['id']}")
                    all_live.append(ch)
                except Exception as exc:  # noqa: BLE001
                    report["failed"].append(f"canal:{cname}:{exc}")

            role_id = None
            try:
                rid, origin = await self.find_or_create_role(guild_id, "Buscando Partida")
                role_id = rid
                if origin == "reused":
                    report["reused"].append(f"rol:{role_id}")
                else:
                    report["created"].append(f"rol:{role_id}")
            except Exception as exc:  # noqa: BLE001
                report["failed"].append(f"rol:{exc}")

            return channels, role_id, report
        except Exception as exc:
            report["failed"].append(f"categoria:error:{exc}")
            return {}, None, report
