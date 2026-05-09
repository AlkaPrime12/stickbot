from app.bot.client import run_bot
from app.logging_config import setup_logging


if __name__ == "__main__":
    setup_logging()
    run_bot()
