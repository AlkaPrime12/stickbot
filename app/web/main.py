import os
import secrets
from contextlib import asynccontextmanager
from urllib.parse import quote, urlencode

import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import get_connection
from app.message_defaults import MESSAGE_TEMPLATE_KEYS, MESSAGE_TEMPLATE_HELP
from app.repositories.player_repository import PlayerRepository
from app.services.guild_config_service import GuildConfigService
from app.services.discord_setup_service import DiscordSetupService
from app.services.message_template_service import MessageTemplateService


def _session_https_only() -> bool:
    """
    Cookies Secure: solo con HTTPS. En http://localhost NO usar Secure o el navegador no guarda sesión.
    Forzar: SESSION_HTTPS_ONLY=1 en producción con URL https.
    Desarrollo local: SESSION_ALLOW_HTTP_COOKIES=1 (por defecto activa si APP_BASE_URL es localhost).
    """
    if os.getenv("SESSION_ALLOW_HTTP_COOKIES", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("SESSION_HTTPS_ONLY", "").lower() in ("1", "true", "yes"):
        return True
    if os.getenv("SESSION_HTTPS_ONLY", "").lower() in ("0", "false", "no"):
        return False
    base = (settings.app_base_url or "").lower()
    if "localhost" in base or "127.0.0.1" in base:
        return False
    return os.getenv("ENV", "").lower() in ("production", "prod")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Misma BD que el bot: crea tablas y migraciones al levantar el panel (Railway / Docker)."""
    from database import inicializar_db

    inicializar_db(settings.database_path)
    yield


app = FastAPI(title="StickBot Setup Panel", lifespan=_lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=_session_https_only(),
)
templates = Jinja2Templates(directory="app/web/templates")
guild_cfg_service = GuildConfigService()
discord_setup_service = DiscordSetupService()
message_template_service = MessageTemplateService()


def _health_payload() -> dict:
    sample_err = None
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT guild_id, last_ocr_error FROM guild_config
                WHERE last_ocr_error IS NOT NULL AND trim(last_ocr_error) != ''
                LIMIT 1
                """
            ).fetchone()
            if row:
                sample_err = {"guild_id": row[0], "message": (row[1] or "")[:300]}
    except Exception:
        pass
    weak_session = settings.session_secret in ("", "change-this-session-secret")
    return {
        "status": "ok",
        "bot_token_configured": bool(settings.discord_token),
        "oauth_client_configured": bool(settings.discord_client_id and settings.discord_client_secret),
        "oauth_redirect_uri": settings.discord_redirect_uri,
        "app_base_url": settings.app_base_url,
        "database_path_configured": bool(settings.database_path),
        "sample_last_ocr_error": sample_err,
        "session_secret_strong": not weak_session,
    }


def _sanitize_csv_channels(s: str) -> str:
    parts = [p.strip() for p in (s or "").replace(";", ",").split(",")]
    return ",".join(p for p in parts if p)


async def _fetch_discord_guild_list(request: Request) -> tuple[list[dict], str | None]:
    """
    Obtiene guilds desde la API de Discord (no guarda en sesión: evita superar el límite ~4KB del cookie).
    """
    token = request.session.get("oauth_token")
    if not token:
        return [], "no_token"
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get(
            "https://discord.com/api/v10/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 401:
            request.session.pop("oauth_token", None)
            request.session.pop("guilds", None)
            request.session.pop("user", None)
            return [], "token_expired"
        if not r.is_success:
            return [], f"discord_http_{r.status_code}"
        guilds = r.json()
    if not isinstance(guilds, list):
        return [], "invalid_response"
    guilds.sort(key=lambda g: (g.get("name") or "").lower())
    return guilds, None


def _collect_channel_ids(payload: dict) -> list[str]:
    keys = [
        "channel_buzon_id",
        "channel_registro_id",
        "channel_historial_id",
        "channel_general_id",
        "channel_busqueda_id",
    ]
    out: list[str] = []
    for k in keys:
        v = payload.get(k)
        if v not in (None, "", 0, "0"):
            out.append(str(v).strip())
    for prefix in (
        "cmd_registrar",
        "cmd_renombrar",
        "cmd_perfil",
        "cmd_stickleaderboard",
        "cmd_partida",
    ):
        csv = payload.get(f"{prefix}_allowed_channels") or ""
        for part in csv.replace(";", ",").split(","):
            p = part.strip()
            if p.isdigit():
                out.append(p)
    seen: set[str] = set()
    deduped: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


@app.get("/health")
async def health():
    return _health_payload()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    request.session.pop("guilds", None)
    user = request.session.get("user")
    login_msg = request.query_params.get("login")
    oauth_logged_in = bool(request.session.get("oauth_token"))
    return templates.TemplateResponse(
        name="home.html",
        context={
            "request": request,
            "user": user,
            "invite_url": _bot_invite_url(),
            "session_expired": login_msg == "expired",
            "login_error": login_msg if login_msg and login_msg not in ("expired",) else None,
            "login_detail": request.query_params.get("detail", ""),
            "oauth_logged_in": oauth_logged_in,
            "redirect_uri_hint": settings.discord_redirect_uri,
            "oauth_configured": bool(settings.discord_client_id and settings.discord_client_secret),
        },
        request=request,
    )


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_global_page(request: Request):
    repo = PlayerRepository()
    rows = repo.top_players_global(100)
    total = repo.count_global_rows()
    return templates.TemplateResponse(
        "leaderboard_global.html",
        context={"request": request, "rows": rows, "total": total},
        request=request,
    )


@app.get("/api/leaderboard/global")
async def api_leaderboard_global(limit: int = 100, offset: int = 0):
    repo = PlayerRepository()
    rows = repo.top_players_global(min(limit, 500), offset)
    total = repo.count_global_rows()
    return {
        "total": total,
        "rows": [
            {"guild_id": r[0], "guild_label": r[1], "player": r[2], "mmr": round(float(r[3]), 1)}
            for r in rows
        ],
    }


@app.get("/overview", response_class=HTMLResponse)
async def overview(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        name="overview.html",
        context={
            "request": request,
            "user": user,
            "health": _health_payload(),
            "invite_url": _bot_invite_url(),
            "redirect_uri": settings.discord_redirect_uri,
        },
        request=request,
    )


@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    return templates.TemplateResponse(
        name="security.html",
        context={
            "request": request,
            "user": request.session.get("user"),
            "session_https": _session_https_only(),
        },
        request=request,
    )


@app.get("/auth/login")
async def auth_login(request: Request):
    if not settings.discord_client_id or not settings.discord_client_secret:
        return RedirectResponse("/?login=no_oauth_config")
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
async def auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    if error:
        detail = (error_description or error)[:300]
        return RedirectResponse(f"/?login=discord_error&detail={quote(detail)}")
    if not code:
        return RedirectResponse("/?login=missing_code")
    if not state or state != request.session.get("oauth_state"):
        # Links guardados de Discord tienen un state viejo; siempre entrar desde "Login" en esta web.
        return RedirectResponse("/?login=bad_state")

    try:
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

            user_resp = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {token}"},
            )
            guilds_resp = await client.get(
                "https://discord.com/api/users/@me/guilds",
                headers={"Authorization": f"Bearer {token}"},
            )
            user_resp.raise_for_status()
            guilds_resp.raise_for_status()
    except Exception:
        return RedirectResponse("/?login=token_exchange_failed")

    request.session["oauth_token"] = token
    request.session["user"] = user_resp.json()
    request.session.pop("guilds", None)
    return RedirectResponse("/setup")


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    if "oauth_token" not in request.session:
        return RedirectResponse("/")
    # Limpia datos viejos que hinchaban la cookie
    request.session.pop("guilds", None)
    guilds, guilds_error = await _fetch_discord_guild_list(request)
    if guilds_error == "token_expired":
        return RedirectResponse("/?login=expired")
    return templates.TemplateResponse(
        name="setup.html",
        context={
            "request": request,
            "guilds": guilds,
            "guilds_error": guilds_error,
        },
        request=request,
    )


@app.get("/setup/{guild_id}", response_class=HTMLResponse)
async def setup_guild_page(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return RedirectResponse("/")
    config = guild_cfg_service.get_or_default(guild_id)
    saved = request.query_params.get("saved") == "1"
    merged = message_template_service.get_all_merged(guild_id)
    template_rows = [
        {"key": k, "text": merged.get(k, ""), "help": MESSAGE_TEMPLATE_HELP.get(k, "")}
        for k in MESSAGE_TEMPLATE_KEYS.keys()
    ]
    return templates.TemplateResponse(
        name="guild_setup.html",
        context={
            "request": request,
            "guild_id": guild_id,
            "config": config,
            "saved": saved,
            "guild_nav_id": guild_id,
            "discord_redirect_uri": settings.discord_redirect_uri,
            "template_rows": template_rows,
        },
        request=request,
    )


@app.post("/setup/{guild_id}/manual")
async def setup_manual(
    guild_id: str,
    guild_display_name: str = Form(""),
    limits_apply_non_admin_only: int = Form(0),
    bot_admin_ids: str = Form(""),
    channel_buzon_id: str = Form(""),
    channel_registro_id: str = Form(""),
    channel_historial_id: str = Form(""),
    channel_general_id: str = Form(""),
    channel_busqueda_id: str = Form(""),
    role_buscando_id: str = Form(""),
    cooldown_minutes: int = Form(22),
    daily_limit: int = Form(3),
    timezone: str = Form("UTC"),
    language: str = Form("es"),
    cmd_registrar_enabled: int = Form(1),
    cmd_registrar_require_channel: int = Form(0),
    cmd_registrar_allowed_channels: str = Form(""),
    cmd_renombrar_enabled: int = Form(1),
    cmd_renombrar_require_channel: int = Form(0),
    cmd_renombrar_allowed_channels: str = Form(""),
    cmd_perfil_enabled: int = Form(1),
    cmd_perfil_require_channel: int = Form(0),
    cmd_perfil_allowed_channels: str = Form(""),
    cmd_stickleaderboard_enabled: int = Form(1),
    cmd_stickleaderboard_require_channel: int = Form(0),
    cmd_stickleaderboard_allowed_channels: str = Form(""),
    cmd_partida_enabled: int = Form(1),
    cmd_partida_require_channel: int = Form(0),
    cmd_partida_allowed_channels: str = Form(""),
    ansi_enabled: int = Form(1),
    ansi_preset: str = Form("default"),
    ocr_confidence_threshold: float = Form(0.25),
    ocr_min_points: int = Form(30),
    ocr_margin_percent: float = Form(20.0),
    ocr_center_confidence: float = Form(0.25),
    ocr_corner_confidence: float = Form(0.10),
    ocr_color_distance_max: float = Form(170.0),
    host_penalty_percent: float = Form(8.0),
    mmr_k_factor: float = Form(32.0),
    partida_confirm_reaction: int = Form(0),
):
    guild_cfg_service.save(
        guild_id,
        {
            "guild_display_name": guild_display_name or "",
            "limits_apply_non_admin_only": limits_apply_non_admin_only,
            "bot_admin_ids": _sanitize_csv_channels(bot_admin_ids),
            "channel_buzon_id": channel_buzon_id or None,
            "channel_registro_id": channel_registro_id or None,
            "channel_historial_id": channel_historial_id or None,
            "channel_general_id": channel_general_id or None,
            "channel_busqueda_id": channel_busqueda_id or None,
            "role_buscando_id": role_buscando_id or None,
            "cooldown_minutes": cooldown_minutes,
            "daily_limit": daily_limit,
            "auto_mode": 0,
            "timezone": timezone,
            "language": language,
            "cmd_registrar_enabled": cmd_registrar_enabled,
            "cmd_registrar_require_channel": cmd_registrar_require_channel,
            "cmd_registrar_allowed_channels": _sanitize_csv_channels(cmd_registrar_allowed_channels),
            "cmd_renombrar_enabled": cmd_renombrar_enabled,
            "cmd_renombrar_require_channel": cmd_renombrar_require_channel,
            "cmd_renombrar_allowed_channels": _sanitize_csv_channels(cmd_renombrar_allowed_channels),
            "cmd_perfil_enabled": cmd_perfil_enabled,
            "cmd_perfil_require_channel": cmd_perfil_require_channel,
            "cmd_perfil_allowed_channels": _sanitize_csv_channels(cmd_perfil_allowed_channels),
            "cmd_stickleaderboard_enabled": cmd_stickleaderboard_enabled,
            "cmd_stickleaderboard_require_channel": cmd_stickleaderboard_require_channel,
            "cmd_stickleaderboard_allowed_channels": _sanitize_csv_channels(cmd_stickleaderboard_allowed_channels),
            "cmd_partida_enabled": cmd_partida_enabled,
            "cmd_partida_require_channel": cmd_partida_require_channel,
            "cmd_partida_allowed_channels": _sanitize_csv_channels(cmd_partida_allowed_channels),
            "ansi_enabled": ansi_enabled,
            "ansi_preset": (ansi_preset or "default").strip() or "default",
            "ocr_confidence_threshold": ocr_confidence_threshold,
            "ocr_min_points": ocr_min_points,
            "ocr_margin_percent": ocr_margin_percent,
            "ocr_center_confidence": ocr_center_confidence,
            "ocr_corner_confidence": ocr_corner_confidence,
            "ocr_color_distance_max": ocr_color_distance_max,
            "host_penalty_percent": host_penalty_percent,
            "mmr_k_factor": mmr_k_factor,
            "partida_confirm_reaction": partida_confirm_reaction,
        },
    )
    return RedirectResponse(f"/setup/{guild_id}?saved=1", status_code=303)


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


@app.get("/api/guilds")
async def api_guilds(request: Request):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    guilds, err = await _fetch_discord_guild_list(request)
    if err == "token_expired":
        return JSONResponse({"error": "token_expired"}, status_code=401)
    if err and err != "no_token":
        return JSONResponse({"error": err, "guilds": guilds}, status_code=502)
    return guilds


@app.get("/api/guilds/{guild_id}/config")
async def api_get_guild_config(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return guild_cfg_service.get_or_default(guild_id)


@app.put("/api/guilds/{guild_id}/config")
async def api_put_guild_config(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await request.json()
    if isinstance(payload.get("cmd_registrar_allowed_channels"), str):
        payload["cmd_registrar_allowed_channels"] = _sanitize_csv_channels(payload["cmd_registrar_allowed_channels"])
    for key in list(payload.keys()):
        if key.endswith("_allowed_channels") and isinstance(payload[key], str):
            payload[key] = _sanitize_csv_channels(payload[key])
    return guild_cfg_service.save(guild_id, payload)


@app.get("/api/guilds/{guild_id}/message-templates")
async def api_get_message_templates(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return message_template_service.get_all_merged(guild_id)


@app.put("/api/guilds/{guild_id}/message-templates")
async def api_put_message_templates(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await request.json()
    if not isinstance(payload, dict):
        return JSONResponse({"error": "invalid_json"}, status_code=400)
    filtered = {k: str(v)[:1900] for k, v in payload.items() if k in MESSAGE_TEMPLATE_KEYS}
    message_template_service.save_partial(guild_id, filtered)
    return message_template_service.get_all_merged(guild_id)


@app.post("/api/guilds/{guild_id}/config/validate")
async def api_validate_config(request: Request, guild_id: str):
    if "oauth_token" not in request.session:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await request.json()
    if not isinstance(payload, dict):
        payload = {}

    checks: list[dict] = []
    ids = _collect_channel_ids(payload)
    if not settings.discord_token:
        return {
            "valid": False,
            "error": "bot_token_missing",
            "message": "Configura DISCORD_TOKEN para validar canales contra la API de Discord.",
            "checks": [],
        }

    async with httpx.AsyncClient(timeout=15) as client:
        headers = {"Authorization": f"Bot {settings.discord_token}"}
        for cid in ids:
            try:
                r = await client.get(f"https://discord.com/api/v10/channels/{cid}", headers=headers)
                ok = r.status_code == 200
                detail: str | None = None
                if ok:
                    try:
                        data = r.json()
                        detail = data.get("name") if isinstance(data, dict) else None
                    except Exception:  # noqa: BLE001
                        detail = None
                else:
                    detail = f"HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001
                ok = False
                detail = str(e)
            checks.append({"channel_id": cid, "ok": ok, "detail": detail})

    channel_fields_filled = sum(
        1
        for k in (
            "channel_buzon_id",
            "channel_registro_id",
            "channel_historial_id",
            "channel_general_id",
            "channel_busqueda_id",
        )
        if payload.get(k) not in (None, "", "0")
    )
    return {
        "valid": len(checks) == 0 or all(c["ok"] for c in checks),
        "guild_id": guild_id,
        "checks": checks,
        "channel_fields_filled": channel_fields_filled,
        "note": "Lista todos los IDs configurados (principales + CSV por comando) y verifica que el bot pueda verlos.",
    }


def _bot_invite_url():
    params = urlencode(
        {
            "client_id": settings.discord_client_id,
            "scope": "bot applications.commands",
            "permissions": "268445712",
        }
    )
    return f"https://discord.com/oauth2/authorize?{params}"
