import os

from alembic import command
from alembic.config import Config
from sqlalchemy import URL

from app.core import logger, settings


def run_migrations() -> None:
    project_root = os.getcwd()
    alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))

    db_url_str = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.DB_USER,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        password=settings.DB_PASSWORD,
    ).render_as_string(hide_password=False).replace("%", "%%")

    alembic_cfg.set_main_option("sqlalchemy.url", db_url_str)
    logger.info("Running Alembic migrations...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations complete.")
