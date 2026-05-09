import os
import shutil
from datetime import datetime


def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "stickbot.db")
    backup_dir = os.path.join(base_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(backup_dir, f"stickbot_{stamp}.db")
    shutil.copy2(db_path, dst)
    print(f"Backup created: {dst}")


if __name__ == "__main__":
    run()
