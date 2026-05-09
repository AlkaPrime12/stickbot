# StickBot Current Logic Spec (Baseline)

This document freezes current behavior so the modular rewrite keeps the same product logic.

## Core commands and behavior

- `!registrar <steam_name>`:
  - Allowed only in register channel.
  - Truncates game name to 15 chars.
  - Inserts player with default MMR 400.
  - Attempts to sync Discord nickname.
- `!renombrar <new_name>`:
  - Requires existing registration.
  - Updates only `nombre_juego`.
  - Preserves MMR/history.
- `!partida [@host]`:
  - Allowed only in match inbox channel.
  - Requires screenshot attachment.
  - Runs OCR pipeline from `lector.py`.
  - Host leveling: subtract 8% points if host appears in OCR results.
  - Updates MMR using Elo-like pairwise formula.
  - Writes `partidas` and `detalles_partida`.
  - Enforces cooldown + daily limit for non-admin users.
- `!perfil`:
  - Shows display summary, current MMR, rank position, daily usage.
- `!stickleaderboard`:
  - Top 15 by MMR descending.
- `!rol`:
  - Toggle role for temporary match notifications.
  - Auto-removes role after 3 hours.
- `!buscarpartida`:
  - Creates LFG interactive message with max 4 players.

## Event behavior

- `on_member_join`: posts onboarding message in general channel.
- `on_message`:
  - Match inbox channel accepts only `!partida`.
  - Register channel accepts only `!registrar`.

## Data behavior

- DB tables in use:
  - `jugadores`
  - `partidas`
  - `detalles_partida`
  - `limite_diario`
- Current DB engine: SQLite (`stickbot.db`).

## Configuration currently hardcoded

- Channel IDs:
  - Register
  - Match inbox
  - History
  - General
  - Search/LFG
- Role ID:
  - Looking-for-game role.
- Admin IDs list.

## Compatibility target

The rewrite must preserve:

1. Match scoring and MMR update logic.
2. OCR-first ingestion workflow.
3. Channel guardrails for register and match inbox.
4. Cooldown and per-day usage limits.
5. Host leveling penalty behavior.
