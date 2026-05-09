import subprocess
import sys


def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "web"):
        subprocess.Popen([sys.executable, "run_web.py"])
        print("Web panel started.")
    if mode in ("all", "bot"):
        subprocess.Popen([sys.executable, "run_bot.py"])
        print("Bot started.")


if __name__ == "__main__":
    run()
