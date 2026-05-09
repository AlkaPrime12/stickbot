# Inventario de SQL táctico en StickBot

Todas las rutas nuevas pasan por `app/db.py` (**placeholders `:nombre`** + `dict` de parámetros).

| Área | Archivos |
|------|----------|
| Conexión / transacciones | [`app/db.py`](../app/db.py), [`app/database_engine.py`](../app/database_engine.py) |
| Repositorios | [`app/repositories/guild_config_repository.py`](../app/repositories/guild_config_repository.py), [`app/repositories/player_repository.py`](../app/repositories/player_repository.py), [`app/repositories/message_template_repository.py`](../app/repositories/message_template_repository.py) |
| Servicios | [`app/services/match_service.py`](../app/services/match_service.py) |
| Panel / health | [`app/web/main.py`](../app/web/main.py) (consultas mínimas en `_health_payload`) |
| OCR | [`lector.py`](../lector.py) ya no usa `sqlite3`; nombres vía [`PlayerRepository`](../app/repositories/player_repository.py) cuando aplica |

## Solo SQLite legacy (sin `DATABASE_URL`)

- [`database.py`](../database.py) — DDL inicial + índices básicos
- [`app/db_migrations.py`](../app/db_migrations.py) — `PRAGMA`, `ALTER` idempotentes; **no ejecutar rutas Postgres**
- Scripts operativos viejos (`scripts/migrate.py`, `scripts/seed.py`) — siguen abriendo `sqlite3`; usar solo modo archivo local

Postgres debe usar **solo** Alembic ([`alembic/versions/`](../alembic/versions/)).
