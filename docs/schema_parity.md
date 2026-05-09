# Paridad `database.py` (SQLite) ↔ Alembic `001_postgres_initial`

La migración [`alembic/versions/001_postgres_initial.py`](../alembic/versions/001_postgres_initial.py) replica el DDL de [`database.py`](../database.py) para:

- `jugadores`, `partidas` (+ `guild_id` en Postgres desde el inicio), `detalles_partida`, `limite_diario`
- `guild_config` — columnas alineadas con [`app/guild_config_columns.py`](../app/guild_config_columns.py) y el `CREATE` en `database.py`
- `guild_admins`, `setup_runs`, `bot_permissions_audit`
- `guild_player_stats` — en SQLite se añade vía [`app/db_migrations.py`](../app/db_migrations.py); en Postgres FK a `jugadores`
- `guild_message_templates` — en SQLite vía `db_migrations`; en Postgres en la migración inicial

Índices extra en Postgres (consultas calientes / OCR): `idx_jugadores_nombre_juego`, `idx_gps_discord_user`, más los existentes en `guild_player_stats` y `limite_diario`.

Diferencias aceptadas:

- `partidas.id_partida` y PKs autogeneradas usan `Identity` en Postgres y `AUTOINCREMENT` en SQLite (ambos permiten `RETURNING id_partida` en el stack actual).
- Tipos `TIMESTAMP`/`DateTime` pueden variar en representación interna; la app pasa fechas como ISO en inserciones críticas.
