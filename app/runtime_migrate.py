"""Bootstrap de esquema al arrancar: Alembic si hay Postgres, SQLite legacy si no."""
from __future__ import annotations

import logging

from app.config import settings, uses_postgresql

logger = logging.getLogger(__name__)


def ensure_schema() -> None:
    if uses_postgresql():
        import pathlib

        from alembic import command
        from alembic.config import Config

        root = pathlib.Path(__file__).resolve().parent.parent
        ini = root / "alembic.ini"
        if not ini.is_file():
            raise RuntimeError(f"No se encuentra alembic.ini en {ini}")
        cfg = Config(str(ini))
        logger.info("Aplicando migraciones Alembic (Postgres)...")
        command.upgrade(cfg, "head")
        logger.info("Migraciones aplicadas.")
        return

    from database import inicializar_db

    logger.info("Inicializando SQLite en %s", settings.database_path)
    inicializar_db(settings.database_path)
