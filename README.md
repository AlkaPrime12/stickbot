# StickBot Discord (Web + Bot)

StickBot ahora incluye:

- Bot Discord para Stick Fight (MMR, OCR, ranking, LFG).
- Panel web para configurar cada servidor Discord.
- Setup manual o automatico de canales/rol.
- Despliegue rapido con Docker Compose.

## 1) Requisitos

- Python 3.11+
- App de Discord creada en Developer Portal
- `DISCORD_TOKEN`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`

## 2) Configuracion

Copiar variables base:

```bash
python scripts/bootstrap.py
```

Editar `.env` y completar:

```env
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
APP_BASE_URL=http://localhost:8000
SESSION_SECRET=change-this-secret
# Producción HTTPS: cookies de sesión seguras
# ENV=production
# SESSION_HTTPS_ONLY=1
DATABASE_PATH=stickbot.db
GIT_AUTO_SYNC=0
GIT_AUTO_SYNC_REMOTE=origin
GIT_AUTO_SYNC_BRANCH=main
GIT_AUTO_SYNC_MESSAGE=auto-sync run_all
```

## 3) Instalacion local (sin Docker)

```bash
pip install -r requirements.txt
python scripts/migrate.py
python run_all.py
```

Esto inicia web + bot al mismo tiempo.

## 4) Instalacion con Docker Compose (recomendada)

```bash
docker compose up --build
```

Servicios:

- Web panel: `http://localhost:8000`
- Bot: corre en contenedor `bot`

## 5) Flujo de setup

1. Abrir `http://localhost:8000`.
2. Invitar bot al servidor.
3. Login Discord desde el panel.
4. Elegir servidor (guild).
5. **Manage** por servidor (`/setup/{guild_id}`): General, canales, límites, políticas por comando, OCR/MMR, apariencia ANSI.
   - Manual: pegar IDs de canales/rol o usar validación API (`POST /api/guilds/{id}/config/validate`).
   - Automático: el bot crea categoría + canales + rol.
6. Probar comandos en Discord según políticas (`enabled` / `require_channel` / CSV).

## 6) Comandos de bot

Slash commands principales:

- `/registrar`
- `/renombrar`
- `/partida`
- `/perfil`
- `/stickleaderboard`

## 7) Scripts operativos

- `python scripts/migrate.py`
- `python scripts/seed.py`
- `python scripts/start.py`
- `python scripts/backup.py`
- `python run_all.py` (web + bot juntos)
- `GIT_AUTO_SYNC=1 python run_all.py` (auto add/commit/push en inicio)

## 8) API de gestión (resumen)

- `GET /health` — estado del despliegue, token bot, OAuth, muestra opcional de último error OCR en BD.
- `GET /api/guilds` — requiere sesión OAuth; lista guilds del usuario.
- `GET/PUT /api/guilds/{guild_id}/config` — lectura/escritura de `guild_config`.
- `GET/PUT /api/guilds/{guild_id}/message-templates` — plantillas de texto del bot (claves en [app/message_defaults.py](app/message_defaults.py)).
- `POST /api/guilds/{guild_id}/config/validate` — comprueba IDs de canal contra Discord (token del **bot**).
- `GET /leaderboard` — página **Leaderboard global** (todos los servidores).
- `GET /api/leaderboard/global` — JSON del ranking global (`guild_player_stats`).

## 9) Notas

- **MMR por servidor:** tabla `guild_player_stats`; `/stickleaderboard` solo lista el guild actual; la web global agrega todos los servidores.
- MMR en partidas usa `mmr_k_factor` y `host_penalty_percent` por servidor.
- OCR: márgenes y umbrales desde Manage; **nunca** se puntúa partida sin imagen → OCR.
- Mensajes ANSI (`ansi_preset`): bloques ```ansi```; mejor en Discord escritorio. Referencia de colores: [Rebane](https://rebane2001.com/discord-colored-text-generator).
- Nunca commitear `.env` ni exponer token/secret en el panel.
- `docs/config_map.md`, `docs/ocr_flow.md`, `docs/extensibility_slash.md` — referencia rápida.
- `docs/current_logic_spec.md` documenta el comportamiento baseline.
- `docs/qa_checklist.md` lista pruebas de regresión recomendadas.
