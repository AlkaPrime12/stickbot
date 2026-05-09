# Mapa de configuración

| Origen | Qué es |
|--------|--------|
| `.env` / [app/config.py](../app/config.py) | `DISCORD_TOKEN`, OAuth client id/secret/redirect, `SESSION_SECRET`, **`DATABASE_URL`** (Postgres recomendado) o **`DATABASE_PATH`** (SQLite si no hay URL), `APP_BASE_URL`, pool opcional `DB_*`, límites por defecto (`DEFAULT_*`). No editables desde el panel por seguridad. |
| Tabla `guild_config` | Canales, políticas por comando (`cmd_*`), OCR/MMR, `ansi_preset`, errores OCR, etc. Editables en **Manage** y `PUT /api/guilds/{id}/config`. |
| `guild_message_templates` | Textos del bot por clave (`registrar_ok`, …). Editables pestaña Mensajes + `PUT /api/guilds/{id}/message-templates`. |
| `guild_player_stats` | MMR por `(guild_id, discord_user_id)`. Actualizado por partidas; leaderboard Discord filtra por guild; web global usa todas las filas. |
| `jugadores` | Identidad: Discord ID ↔ nombre de juego (compartido entre guilds). |
