from logging.config import fileConfig

from alembic import context

from app.database_engine import engine as app_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_online() -> None:
    with app_engine.connect() as connection:
        context.configure(connection=connection, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Alembic offline no está soportado; usá DATABASE_URL y upgrade online.")

run_migrations_online()
