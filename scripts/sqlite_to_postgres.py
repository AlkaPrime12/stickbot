"""
Copia datos de una SQLite existente hacia Postgres (DATABASE_URL).

Requisitos:
  - Postgres vacío con esquema ya aplicado: `alembic upgrade head`
  - variable de entorno DATABASE_URL apuntando al Postgres destino

Orden respeta FKs. Uso típico (Railway): dump datos locales → import a Postgres addon.

  python scripts/sqlite_to_postgres.py --sqlite ./stickbot.db
  python scripts/sqlite_to_postgres.py --sqlite ./stickbot.db --dry-run
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import create_engine, text

from app.database_engine import _normalize_postgres_url

# Orden topológico (tablas hijas después de padres).
_COPY_ORDER: tuple[str, ...] = (
    "jugadores",
    "guild_config",
    "limite_diario",
    "guild_admins",
    "setup_runs",
    "bot_permissions_audit",
    "partidas",
    "guild_player_stats",
    "guild_message_templates",
    "detalles_partida",
)


def _table_exists_sq(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def _mask_url(raw: str) -> str:
    try:
        p = urlparse(raw if "://" in raw else f"postgresql://{raw}")
        host = p.hostname or "?"
        db = (p.path or "").lstrip("/") or "?"
        return f"{p.scheme or 'postgresql'}@{host}:{p.port or 'default'}/{db}"
    except Exception:
        return "(configured)"


def copy_rows(
    sqlite_path: Path,
    database_url: str,
    *,
    dry_run: bool,
) -> None:
    if not sqlite_path.is_file():
        raise SystemExit(f"No existe archivo SQLite: {sqlite_path}")

    safe = _mask_url(database_url)
    print(f"Origen SQLite: {sqlite_path}")
    print(f"Destino Postgres: {safe} (contraseña no mostrada)")
    print(f"Dry-run: {dry_run}")

    sq = sqlite3.connect(str(sqlite_path))
    sq.row_factory = sqlite3.Row

    if dry_run:
        for t in _COPY_ORDER:
            if not _table_exists_sq(sq, t):
                print(f"  [skip] {t} (no en SQLite)")
                continue
            n = sq.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"]
            print(f"  {t}: {n} filas")
        sq.close()
        return

    engine = create_engine(_normalize_postgres_url(database_url))

    copied = 0
    try:
        for t in _COPY_ORDER:
            if not _table_exists_sq(sq, t):
                print(f"  [skip] {t} (no en SQLite)")
                continue
            cur = sq.execute(f"SELECT * FROM {t}")
            rows = cur.fetchall()
            if not rows:
                print(f"  {t}: 0 filas")
                continue
            cols = [d[0] for d in cur.description]
            col_list = ", ".join(cols)
            placeholders = ", ".join(":" + c for c in cols)
            insert_sql = f"INSERT INTO {t} ({col_list}) VALUES ({placeholders})"
            dict_rows = [{cols[i]: row[i] for i in range(len(cols))} for row in rows]
            with engine.begin() as conn:
                for d in dict_rows:
                    conn.execute(text(insert_sql), d)
            copied += len(dict_rows)
            print(f"  {t}: {len(dict_rows)} filas insertadas")
    finally:
        sq.close()

    print(f"Listo. Total filas escritas (suma por tabla): ~{copied}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Copia SQLite → Postgres (DATABASE_URL)")
    ap.add_argument(
        "--sqlite",
        default=os.getenv("SQLITE_SOURCE", "stickbot.db"),
        help="Ruta al .db SQLite fuente",
    )
    ap.add_argument("--dry-run", action="store_true", help="Solo contar filas, no escribir")
    args = ap.parse_args()

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not args.dry_run and not url:
        print("DATABASE_URL debe estar definido (Postgres destino).", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        url = url or "postgresql://dry-run-only@localhost:5432/example"

    copy_rows(Path(args.sqlite).resolve(), url, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
