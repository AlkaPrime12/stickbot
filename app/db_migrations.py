"""Idempotent SQLite column additions shared by scripts/migrate.py and database.py."""
import sqlite3


def ensure_guild_scoped_mmr(conn: sqlite3.Connection) -> None:
    """Tabla guild_player_stats + guild_id en partidas; backfill desde jugadores si vacío."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_player_stats (
            guild_id TEXT NOT NULL,
            discord_user_id TEXT NOT NULL,
            mmr REAL DEFAULT 400.0,
            PRIMARY KEY (guild_id, discord_user_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_gps_guild_mmr ON guild_player_stats(guild_id, mmr DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_gps_mmr ON guild_player_stats(mmr DESC)"
    )

    cols = {r[1] for r in conn.execute("PRAGMA table_info(partidas)").fetchall()}
    if "guild_id" not in cols:
        conn.execute("ALTER TABLE partidas ADD COLUMN guild_id TEXT")

    n = conn.execute("SELECT COUNT(*) FROM guild_player_stats").fetchone()[0]
    if n > 0:
        return

    try:
        j_rows = conn.execute("SELECT id_jugador, mmr FROM jugadores").fetchall()
    except sqlite3.OperationalError:
        j_rows = []
    try:
        g_rows = [r[0] for r in conn.execute("SELECT guild_id FROM guild_config").fetchall()]
    except sqlite3.OperationalError:
        g_rows = []
    if g_rows and j_rows:
        for gid in g_rows:
            for uid, mmr in j_rows:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO guild_player_stats (guild_id, discord_user_id, mmr)
                    VALUES (?, ?, ?)
                    """,
                    (str(gid), str(uid), float(mmr)),
                )
    elif j_rows:
        for uid, mmr in j_rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO guild_player_stats (guild_id, discord_user_id, mmr)
                VALUES ('_legacy_', ?, ?)
                """,
                (str(uid), float(mmr)),
            )


def ensure_guild_message_templates_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_message_templates (
            guild_id TEXT NOT NULL,
            template_key TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (guild_id, template_key)
        )
        """
    )


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


def ensure_all_post_schema(conn: sqlite3.Connection) -> None:
    """Ejecutar tras crear tablas base: MMR por guild + plantillas + columnas extendidas."""
    ensure_guild_config_extended_columns(conn)
    ensure_guild_scoped_mmr(conn)
    ensure_guild_message_templates_table(conn)
