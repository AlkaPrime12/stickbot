# StickBot QA Checklist

## Setup validation

- [ ] `python scripts/migrate.py` completes without errors.
- [ ] `/health` returns `{"status":"ok"}`.
- [ ] OAuth login completes and guilds list appears in `/setup`.
- [ ] Bot invite URL adds bot with `bot applications.commands` scopes.

## Manual configuration validation

- [ ] Save manual channel/role IDs for a guild.
- [ ] `/registrar` works only in configured register channel.
- [ ] `/partida` works only in configured match channel.

## Automatic configuration validation

- [ ] Auto setup creates category + required channels.
- [ ] Auto setup creates (or reuses) `Buscando Partida` role.
- [ ] IDs are persisted in `guild_config`.

## Gameplay validation

- [ ] OCR screenshot pipeline returns player results.
- [ ] Host leveling applies 8% reduction.
- [ ] MMR updates and leaderboard reflect latest match.

## Operations validation

- [ ] `python scripts/backup.py` generates DB backup in `backups/`.
- [ ] Bot and web can run simultaneously (`run_bot.py`, `run_web.py`).
