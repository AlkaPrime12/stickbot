import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _derived_redirect_uri() -> str:
    """
    Si DISCORD_REDIRECT_URI no está definido, usar APP_BASE_URL + /auth/callback
    (evita OAuth en producción con redirect localhost por defecto).
    """
    explicit = (os.getenv("DISCORD_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    base = (os.getenv("APP_BASE_URL") or "http://localhost:8000").strip().rstrip("/")
    return f"{base}/auth/callback"


@dataclass
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    discord_client_secret: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    discord_redirect_uri: str = _derived_redirect_uri()
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
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
settings.database_path = _normalize_database_path(settings.database_path)
