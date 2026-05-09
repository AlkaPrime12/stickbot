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
DATABASE_PATH=stickbot.db
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
5. Configurar:
   - Manual: pegar IDs de canales/rol.
   - Automatico: el bot crea categoria + canales + rol.
6. Probar comandos en Discord.

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

## 8) Notas

- Se mantiene la logica central de MMR/OCR del bot original.
- `docs/current_logic_spec.md` documenta el comportamiento baseline.
