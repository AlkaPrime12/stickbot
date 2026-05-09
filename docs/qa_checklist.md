# StickBot QA Checklist

## Migraciones y base de datos

- [ ] `python scripts/migrate.py` completa sin errores (desde la raíz del proyecto).
- [ ] Tras migrar: existen tablas `guild_player_stats` y `guild_message_templates`; `partidas.guild_id` presente.

## Panel web y API

- [ ] `GET /health` incluye `bot_token_configured`, `oauth_client_configured`, `session_secret_strong`, `sample_last_ocr_error` (opcional).
- [ ] OAuth login respeta `state`; callback rechaza estado inválido.
- [ ] Tras login, `/setup` lista guilds y `/setup/{guild_id}` abre Manage.
- [ ] Guardar Manage redirige con `?saved=1` y muestra toast.
- [ ] Botón **Validar canales** en Manage devuelve JSON de comprobaciones (con `DISCORD_TOKEN`).
- [ ] Pestaña Mensajes: **Guardar textos del bot** persiste plantillas (`PUT /api/guilds/{id}/message-templates`).
- [ ] `GET /leaderboard` muestra ranking global; `GET /api/leaderboard/global` devuelve filas.
- [ ] `GET/PUT /api/guilds/{id}/config` y plantillas funcionan con sesión OAuth.

## Políticas por comando

- [ ] `cmd_*_enabled=0` bloquea el comando.
- [ ] `cmd_*_require_channel=0`: comando en cualquier canal.
- [ ] `require_channel=1` + CSV vacío: canal principal configurado.
- [ ] `require_channel=1` + CSV con IDs: solo esos canales.

## Leaderboard y MMR

- [ ] `/stickleaderboard` en un servidor muestra solo jugadores de ese `guild_id`.
- [ ] Web global muestra entradas de todos los guilds (mismo usuario puede repetirse en varios servidores).
- [ ] Tras una partida válida, `guild_player_stats` actualiza MMR del servidor donde se jugó.

## `/partida` y OCR

- [ ] Sin adjunto / no imagen: rechazado.
- [ ] Imagen válida: OCR con parámetros de Manage.
- [ ] Validación `ocr_min_points` y `last_ocr_error` en fallos.
- [ ] Partida OK: MMR y `jugadores.mmr` coherente tras persistencia.

## ANSI

- [ ] Respuestas del bot usan bloque ANSI según `ansi_preset` (probar en Discord desktop).

## Operaciones

- [ ] `python scripts/backup.py` genera backup en `backups/`.
- [ ] `run_all.py` ejecuta web + bot concurrentemente.

## Producción

- [ ] `SESSION_SECRET` distinto del valor por defecto.
- [ ] HTTPS + `ENV=production` o `SESSION_HTTPS_ONLY=1` para cookies `Secure`.
- [ ] `DISCORD_REDIRECT_URI` coincide con la URL pública del panel en el Developer Portal.
