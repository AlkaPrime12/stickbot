import os
from dataclasses import dataclass, field
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _parse_database_url() -> tuple[str | None, str | None]:
    """
    DATABASE_URL opcional (Postgres recomendado en prod compartido).
    Devuelve (url_sin_recortes, etiqueta_segura_sin_password).
    """
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if not raw:
        return None, None
    display = raw
    try:
        p = urlparse(raw if "://" in raw else f"postgresql://{raw}")
        host = p.hostname or "?"
        db = (p.path or "").lstrip("/") or "?"
        display = f"{p.scheme or 'postgresql'}@{host}:{p.port or 'default'}/{db}"
    except Exception:
        display = "(configured)"
    return raw, display


def _resolve_public_base_url() -> str:
    """
    URL pública de la app (sin barra final).
    1) APP_BASE_URL si está definido
    2) Railway: https:// + RAILWAY_PUBLIC_DOMAIN (la da Railway cuando el servicio tiene dominio)
    3) localhost para desarrollo
    """
    explicit = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    rail = (os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if rail:
        return f"https://{rail}"
    return "http://localhost:8000"


def _derived_redirect_uri() -> str:
    """
    Si DISCORD_REDIRECT_URI no está definido: base pública + /auth/callback.
    En Railway suele bastar con no definir nada y tener dominio público + la misma URL en Discord.
    """
    explicit = (os.getenv("DISCORD_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    base = _resolve_public_base_url()
    return f"{base}/auth/callback"


@dataclass
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    discord_client_secret: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    discord_redirect_uri: str = field(default_factory=_derived_redirect_uri)
    app_base_url: str = field(default_factory=_resolve_public_base_url)
    database_url: str | None = None
    database_url_safe_label: str | None = None
    database_path: str = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "stickbot.db"))
    session_secret: str = os.getenv("SESSION_SECRET", "change-this-session-secret")
    default_daily_limit: int = int(os.getenv("DEFAULT_DAILY_LIMIT", "3"))
    default_cooldown_minutes: int = int(os.getenv("DEFAULT_COOLDOWN_MINUTES", "22"))


def _normalize_database_path(path_value: str) -> str:
    # If a Linux container path is set on Windows, fallback to local DB file.
    if os.name == "nt" and path_value.startswith("/"):
        return os.path.join(os.getcwd(), "stickbot.db")
    if not os.path.isabs(path_value):
        return os.path.join(os.getcwd(), path_value)
    return path_value


settings = Settings()
_db_u, _db_lbl = _parse_database_url()
settings.database_url = _db_u
settings.database_url_safe_label = _db_lbl
settings.database_path = _normalize_database_path(settings.database_path)


def uses_postgresql() -> bool:
    return bool(settings.database_url and settings.database_url.strip())
