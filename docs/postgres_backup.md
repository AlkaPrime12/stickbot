# Backup y restore (Postgres Railway / hosting)

Este documento es una guía breve para operadores. Los nombres de menús pueden cambiar según la consola Railway.

## Backup

1. Abrir el recurso **Postgres** del proyecto en Railway (o tu proveedor).
2. Usar **Backups / Snapshots** si el plan lo incluye; descargar cuando la plataforma ofrezca `.sql.gz` o “Export”.
3. Como alternativa, desde tu máquina con `DATABASE_URL` (solo quien debe tener acceso a secretos):
   ```bash
   pg_dump "$DATABASE_URL" --no-owner --format=custom -f stickbot.dump
```
   Para SQL plano:
   ```bash
   pg_dump "$DATABASE_URL" --no-owner -f stickbot.sql
```
   No compartir el archivo: contiene configuración en tablas como `guild_config`.

## Restore

En base **vacía** o nueva (crear addon Postgres fresco), cargar datos:

```bash
pg_restore -d "$DATABASE_URL" --clean --no-owner stickbot.dump
```

Con SQL:

```bash
psql "$DATABASE_URL" -f stickbot.sql
```

Tras cambiar solo el addon, configurar **la misma** variable `DATABASE_URL` en los servicios **web** y **bot** y redeploy para que ejecuten Alembic al iniciar (`ensure_schema`). Si aplicaste dumps generados después de código legacy, revisá compatibilidad de versión de migraciones (`GET /health` muestra revisión alembica en Postgres).

## Rotación de `DATABASE_URL`

Al rotar secretos del proveedor, actualizar **los dos** servicios a la vez; hasta entonces pueden apuntar a bases distintas y el panel Discord no coincidirá con `/stickconfig`.
