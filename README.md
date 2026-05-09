# StickBot Discord (Web + Bot)

StickBot incluye:

- Bot Discord para Stick Fight (MMR, OCR, ranking, LFG).
- Panel web para configurar cada servidor Discord.
- Setup manual o automático de canales/rol.
- **Base unificada (estilo Carl-bot):** Postgres vía **`DATABASE_URL`** compartido entre panel y bot, o modo legado SQLite con **`DATABASE_PATH`**.

## 1) Requisitos

- Python 3.11+
- App de Discord creada en Developer Portal
- `DISCORD_TOKEN`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`

## 2) Configuración

Copiar variables base:

```bash
python scripts/bootstrap.py
```

Editar `.env` — ver [`.env.example`](.env.example). Resumen:

- **`DATABASE_URL` (recomendado en Railway / prod):** URL Postgres. **Definir la misma en el servicio web y en el servicio bot.** Al iniciar ambos ejecutan Alembic (`ensure_schema`).
- **`DATABASE_PATH`:** sólo cuando `DATABASE_URL` está vacío (SQLite local o legado sobre archivo).
- **Pool Postgres (opcional):** `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`.

```env
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
APP_BASE_URL=http://localhost:8000
SESSION_SECRET=change-this-secret
# DATABASE_URL=postgresql://...
DATABASE_PATH=stickbot.db
DEFAULT_DAILY_LIMIT=3
DEFAULT_COOLDOWN_MINUTES=22
GIT_AUTO_SYNC=0
GIT_AUTO_SYNC_REMOTE=origin
GIT_AUTO_SYNC_BRANCH=main
GIT_AUTO_SYNC_MESSAGE=auto-sync run_all
```

## 3) Instalación local (sin Docker)

```bash
pip install -r requirements.txt
# Sin DATABASE_URL — SQLite como antes:
python scripts/migrate.py
# Con Postgres: export DATABASE_URL=... ; luego
alembic upgrade head
python run_all.py
```

Esto puede iniciar web + bot según tus scripts locales.

## 4) Postgres local con Compose (opcional)

```bash
docker compose --profile postgres up postgres -d
# Ejemplo DATABASE_URL contra el contenedor (ajustá credenciales a tu .env):
# DATABASE_URL=postgresql://stickbot:stickbot@127.0.0.1:5432/stickbot
docker compose up --build
```

Dos servicios en la misma imagen pueden usar comandos distintos: ver comentarios en [`Dockerfile`](Dockerfile).

## 5) Flujo de setup

1. Abrir `http://localhost:8000`.
2. Invitar bot al servidor.
3. Login Discord desde el panel.
4. Elegir servidor (guild).
5. **Manage** (`/setup/{guild_id}`): General, canales, límites, políticas por comando, OCR/MMR, apariencia ANSI.
6. Verificar **`/stickconfig`** en Discord y el panel muestran la misma config (debajo: misma **`DATABASE_URL`** o misma **`DATABASE_PATH`** si no usás Postgres).

## 6) Comandos de bot

Slash commands principales: `/registrar`, `/renombrar`, `/partida`, `/perfil`, `/stickleaderboard`, **`/stickconfig`** (solo administradores del servidor o IDs en `bot_admin_ids`) — muestra la config efectiva desde la base en ese momento.

## 7) Scripts operativos

- `python scripts/migrate.py` — migraciones SQLite (legado archivo).
- `alembic upgrade head` — esquema Postgres (también se ejecuta solo al iniciar si hay `DATABASE_URL`).
- [`scripts/sqlite_to_postgres.py`](scripts/sqlite_to_postgres.py) — copiar datos SQLite → Postgres tras `alembic upgrade head`; `--dry-run` para revisar cantidades.
- `python scripts/seed.py`, `python scripts/start.py`, `python scripts/backup.py`, `python run_all.py`

## 8) Railway (Postgres recomendado)

1. Crear addon **PostgreSQL** y copiar `DATABASE_URL` (interna o público según región/red).
2. Pegar **`DATABASE_URL` idéntica** en los servicios **StickBot Web** y **StickBot Bot** (Railway permite la misma variable referenciando el recurso Postgres).
3. Redeploy: al arrancar se aplica **`alembic upgrade head`**.
4. Migrar datos desde una SQLite vieja: `scripts/sqlite_to_postgres.py` contra la URL del addon (véase `--help`).
5. Comprobar `GET /health`: `database_backend`, `database_url_safe_host`, `alembic_revision`.

Backups/restores: [`docs/postgres_backup.md`](docs/postgres_backup.md).

## 9) Cutover rápido (SQLite → Postgres)

1. **`pg_dump` / export** de la SQLite con el script copy o hacer dump lógico vía [`scripts/sqlite_to_postgres.py`](scripts/sqlite_to_postgres.py) hacia Postgres **vacío** ya migrado.
2. Actualizar **`DATABASE_URL`** en **web + bot**.
3. Redeploy ambos procesos.
4. Smoke: `GET /health`, guardar un cambio en **Manage**, comprobar `/stickconfig` y una **partida OCR** opcional si tenés OCR habilitado.

## 10) API de gestión (resumen)

- `GET /health` — backend (`postgresql|sqlite`), host seguro derivado de la URL sin contraseña, revisión Alembic en Postgres, token bot, OAuth, muestra opcional último error OCR.
- REST de guilds, plantillas de mensajes, validate, discord-channels — ver sección equivalente anterior en el código.

## 11) Otros enlaces de documentación

- `docs/config_map.md`, `docs/ocr_flow.md`, `docs/extensibility_slash.md`
- `docs/current_logic_spec.md` — comportamiento baseline
- `docs/qa_checklist.md` — regresión manual
- `docs/sql_style.md`, `docs/sql_audit.md`, `docs/schema_parity.md`

**Notas:** MMR por servidor → `guild_player_stats`. Nunca commitear `.env`. Producción recomendada: **un solo Postgres** en lugar de dos archivos SQLite en volúmenes distintos.
