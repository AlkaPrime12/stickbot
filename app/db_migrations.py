"""Idempotent SQLite column additions shared by scripts/migrate.py and database.py."""
import sqlite3


def ensure_guild_config_extended_columns(conn: sqlite3.Connection) -> None:
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(guild_config)").fetchall()}
    except sqlite3.OperationalError:
        return
    specs = [
        ("guild_display_name", "TEXT DEFAULT ''"),
        ("limits_apply_non_admin_only", "INTEGER DEFAULT 0"),
        ("bot_admin_ids", "TEXT DEFAULT ''"),
        ("mmr_k_factor", "REAL DEFAULT 32.0"),
        ("partida_confirm_reaction", "INTEGER DEFAULT 0"),
        ("ocr_margin_percent", "REAL DEFAULT 20.0"),
        ("ocr_center_confidence", "REAL DEFAULT 0.25"),
        ("ocr_corner_confidence", "REAL DEFAULT 0.10"),
        ("ocr_color_distance_max", "REAL DEFAULT 170.0"),
        ("last_ocr_error", "TEXT"),
        ("ansi_preset", "TEXT DEFAULT 'default'"),
    ]
    for col_name, decl in specs:
        if col_name not in cols:
            conn.execute(f"ALTER TABLE guild_config ADD COLUMN {col_name} {decl}")
