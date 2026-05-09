import os
import sys
import sqlite3

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from app.db_migrations import ensure_guild_config_extended_columns


def run():
    db_path = os.path.join(base_dir, "stickbot.db")
    migrations_dir = os.path.join(base_dir, "migrations")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        applied = {
            row[0]
            for row in conn.execute("SELECT name FROM schema_migrations").fetchall()
        }
        for name in sorted(os.listdir(migrations_dir)):
            if not name.endswith(".sql"):
                continue
            if name in applied:
                print(f"Skipping migration (already applied): {name}")
                continue
            with open(os.path.join(migrations_dir, name), "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.execute(
                "INSERT INTO schema_migrations (name) VALUES (?)",
                (name,),
            )
            print(f"Applied migration: {name}")
        ensure_guild_config_extended_columns(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    run()
