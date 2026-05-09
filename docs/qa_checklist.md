# StickBot QA Checklist

## Migraciones y base de datos

- [ ] `python scripts/migrate.py` completa sin errores (desde la raíz del proyecto).
- [ ] `database.py` / `inicializar_db` añade columnas extendidas de `guild_config` sin fallar en re-ejecución.

## Panel web y API

- [ ] `GET /health` incluye `bot_token_configured`, `oauth_client_configured`, `session_secret_strong`, `sample_last_ocr_error` (opcional).
- [ ] OAuth login respeta `state`; callback rechaza estado inválido.
- [ ] Tras login, `/setup` lista guilds y `/setup/{guild_id}` abre Manage.
- [ ] Guardar Manage redirige con `?saved=1` y muestra toast.
- [ ] `GET/PUT /api/guilds/{id}/config` (con sesión) lee/escribe config completa; CSV de canales permitidos se normaliza.
- [ ] `POST /api/guilds/{id}/config/validate` con `DISCORD_TOKEN` verifica IDs vía API de Discord (200 por canal válido).

## Políticas por comando

- [ ] `cmd_*_enabled=0` bloquea el comando.
- [ ] `cmd_*_require_channel=0`: comando en cualquier canal.
- [ ] `require_channel=1` + CSV vacío: se usa el canal principal configurado (`channel_*_id` correspondiente).
- [ ] `require_channel=1` + CSV con IDs: solo esos canales.

## `/partida` y OCR

- [ ] Sin adjunto: mensaje de advertencia (no procesa).
- [ ] Adjunto no imagen: rechazado.
- [ ] Imagen válida: OCR con parámetros de Manage (`ocr_margin_percent`, umbrales de confianza, `ocr_color_distance_max`, etc.).
- [ ] Resultados por debajo de `ocr_min_points`: error y `last_ocr_error` actualizado en BD.
- [ ] Partida OK: MMR con `mmr_k_factor` y penalización al host según `host_penalty_percent`; `last_ocr_error` limpiado.

## ANSI

- [ ] `ansi_enabled=0`: respuestas texto plano.
- [ ] `ansi_enabled=1` y preset (`default`, `high_contrast`, `muted`, `mono`): bloques ```ansi``` visibles en cliente desktop.

## Operaciones

- [ ] `python scripts/backup.py` genera backup en `backups/`.
- [ ] `run_all.py` ejecuta web + bot concurrentemente.

## Producción

- [ ] `SESSION_SECRET` distinto del valor por defecto.
- [ ] HTTPS + `ENV=production` o `SESSION_HTTPS_ONLY=1` para cookies `Secure`.
- [ ] `DISCORD_REDIRECT_URI` coincide con la URL pública del panel en el Developer Portal.
