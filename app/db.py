import sqlite3
import os
from contextlib import contextmanager
from app.config import settings


@contextmanager
def get_connection():
    db_dir = os.path.dirname(settings.database_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, timeout=10.0)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
