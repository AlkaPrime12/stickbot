"""Motor SQLAlchemy: PostgreSQL (`DATABASE_URL`) o SQLite legacy (`DATABASE_PATH`)."""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from app.config import settings


def _normalize_postgres_url(url: str) -> str:
    """Railway/Dev entregan postgres:// o postgresql://; el proyecto usa sólo psycopg v3."""
    u = url.strip()
    if u.startswith("postgres://"):
        u = "postgresql://" + u[len("postgres://") :]
    if u.startswith("postgresql+"):
        return u
    if u.startswith("postgresql://"):
        return "postgresql+psycopg://" + u[len("postgresql://") :]
    return u


def create_engine_from_settings() -> Engine:
    if settings.database_url:
        url = _normalize_postgres_url(settings.database_url)
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        )
    # SQLite desarrollo local / fallback sin Postgres
    path = settings.database_path.replace("\\", "/")
    return create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False, "timeout": 10},
        poolclass=NullPool,
        pool_pre_ping=True,
    )


engine = create_engine_from_settings()


def dialect_name() -> str:
    return engine.dialect.name


def is_postgresql() -> bool:
    return dialect_name() == "postgresql"
