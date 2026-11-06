import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# ---------------------------------------------------------------------------
# Load environment variables from the project root .env (if present).
# Alembic is typically invoked from backend/, so walk up one level.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env", override=False)
load_dotenv(Path.cwd().parent / ".env", override=False)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Resolve the migrator/app database URLs.
#
# Two supported configuration styles:
#   1. Full URL: DATABASE_URL_MIGRATOR / DATABASE_URL_APP
#      (password must be URL-encoded if it contains special characters)
#   2. Components: DB_MIGRATOR_USER/PASSWORD/HOST/PORT/NAME (and DB_APP_*)
#      (password is auto-URL-encoded here - recommended when passwords contain
#       special characters such as @, :, #, /, ?)
# Component style takes precedence when DB_*_USER is present.
# ---------------------------------------------------------------------------
from urllib.parse import quote_plus


def _build_url(prefix: str) -> str | None:
    """Build a SQLAlchemy URL from DB_<prefix>_* components, or None if not configured."""
    user = os.getenv(f"DB_{prefix}_USER")
    if not user:
        return None
    password = os.getenv(f"DB_{prefix}_PASSWORD", "")
    host = os.getenv(f"DB_{prefix}_HOST", "localhost")
    port = os.getenv(f"DB_{prefix}_PORT", "5432")
    name = os.getenv(f"DB_{prefix}_NAME", "ledgerline_dev")
    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


MIGRATOR_DATABASE_URL = _build_url("MIGRATOR") or os.getenv("DATABASE_URL_MIGRATOR")
if not MIGRATOR_DATABASE_URL:
    raise RuntimeError(
        "Migrator database not configured. Set either DB_MIGRATOR_USER + "
        "DB_MIGRATOR_PASSWORD (recommended) or DATABASE_URL_MIGRATOR in .env."
    )

APP_DATABASE_URL = _build_url("APP") or os.getenv("DATABASE_URL_APP")

# Inject the resolved URL into the Alembic config so offline/online modes use it.
# (Avoid set_main_option: configparser would choke on '%' in URL-encoded passwords.)
# config.set_main_option("sqlalchemy.url", MIGRATOR_DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
# from backend.app.models import Base  # noqa: E402
# target_metadata = Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = MIGRATOR_DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(MIGRATOR_DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
