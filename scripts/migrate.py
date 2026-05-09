import os
import sqlite3


def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "stickbot.db")
    migrations_dir = os.path.join(base_dir, "migrations")
    conn = sqlite3.connect(db_path)
    try:
        for name in sorted(os.listdir(migrations_dir)):
            if not name.endswith(".sql"):
                continue
            with open(os.path.join(migrations_dir, name), "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            print(f"Applied migration: {name}")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    run()
