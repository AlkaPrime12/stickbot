import os
import sqlite3


def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "stickbot.db")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO guild_config (
                guild_id, cooldown_minutes, daily_limit, auto_mode
            ) VALUES (?, 22, 3, 0)
            """,
            ("demo-guild",),
        )
        conn.commit()
        print("Seed complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
