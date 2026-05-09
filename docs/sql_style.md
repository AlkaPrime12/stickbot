# Estilo SQL (StickBot)

- Todas las consultas en repos/servicios usan **`text()`** con parámetros **nombrados** (`:guild_id`), no posicionales `?`.
- No uses `PRAGMA` fuera del camino SQLite legacy (`database.py` / bootstrap local).
- **UPSERT** portable: `ON CONFLICT (...) DO UPDATE` / `DO NOTHING` (Postgres + SQLite ≥ 3.24).
- Inserciones con ID autogenerado: preferir **`RETURNING id_partida`** en `partidas`.
