import secrets
from urllib.parse import urlencode
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.services.guild_config_service import GuildConfigService
from app.services.discord_setup_service import DiscordSetupService

app = FastAPI(title="StickBot Setup Panel")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
templates = Jinja2Templates(directory="app/web/templates")
guild_cfg_service = GuildConfigService()
discord_setup_service = DiscordSetupService()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        name="home.html",
        context={
            "request": request,
            "user": user,
            "invite_url": _bot_invite_url(),
        },
        request=request,
    )


@app.get("/auth/login")
async def auth_login(request: Request):
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    params = urlencode(
        {
            "client_id": settings.discord_client_id,
            "redirect_uri": settings.discord_redirect_uri,
            "response_type": "code",
            "scope": "identify guilds",
            "state": state,
            "prompt": "consent",
        }
    )
    return RedirectResponse(f"https://discord.com/api/oauth2/authorize?{params}")


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str, state: str):
    if state != request.session.get("oauth_state"):
        return JSONResponse({"error": "invalid_oauth_state"}, status_code=400)

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.discord_redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]

        user_resp = await client.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {token}"})
        guilds_resp = await client.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"})
        user_resp.raise_for_status()
        guilds_resp.raise_for_status()

    request.session["oauth_token"] = token
    request.session["user"] = user_resp.json()
    request.session["guilds"] = guilds_resp.json()
    return RedirectResponse("/setup")


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    if "oauth_token" not in request.session:
        return RedirectResponse("/")
    guilds = request.session.get("guilds", [])
    return templates.TemplateResponse(
        name="setup.html",
        context={"request": request, "guilds": guilds},
        request=request,
    )


@app.get("/setup/{guild_id}", response_class=HTMLResponse)
async def setup_guild_page(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return RedirectResponse("/")
    config = guild_cfg_service.get_or_default(guild_id)
    return templates.TemplateResponse(
        name="guild_setup.html",
        context={"request": request, "guild_id": guild_id, "config": config},
        request=request,
    )


@app.post("/setup/{guild_id}/manual")
async def setup_manual(
    guild_id: str,
    channel_buzon_id: str = Form(""),
    channel_registro_id: str = Form(""),
    channel_historial_id: str = Form(""),
    channel_general_id: str = Form(""),
    channel_busqueda_id: str = Form(""),
    role_buscando_id: str = Form(""),
    cooldown_minutes: int = Form(22),
    daily_limit: int = Form(3),
):
    guild_cfg_service.save(
        guild_id,
        {
            "channel_buzon_id": channel_buzon_id or None,
            "channel_registro_id": channel_registro_id or None,
            "channel_historial_id": channel_historial_id or None,
            "channel_general_id": channel_general_id or None,
            "channel_busqueda_id": channel_busqueda_id or None,
            "role_buscando_id": role_buscando_id or None,
            "cooldown_minutes": cooldown_minutes,
            "daily_limit": daily_limit,
            "auto_mode": 0,
        },
    )
    return RedirectResponse(f"/setup/{guild_id}", status_code=303)


@app.post("/setup/{guild_id}/auto")
async def setup_auto(guild_id: str):
    channels, role_id, report = await discord_setup_service.auto_setup(guild_id)
    guild_cfg_service.save(
        guild_id,
        {
            **channels,
            "role_buscando_id": role_id,
            "cooldown_minutes": settings.default_cooldown_minutes,
            "daily_limit": settings.default_daily_limit,
            "auto_mode": 1,
        },
    )
    return report


def _bot_invite_url():
    params = urlencode(
        {
            "client_id": settings.discord_client_id,
            "scope": "bot applications.commands",
            "permissions": "268445712",
        }
    )
    return f"https://discord.com/oauth2/authorize?{params}"
