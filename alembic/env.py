"""
alembic/env.py
 
Configured for async SQLAlchemy with FastAPI.
 
Key differences from the default Alembic env.py:
- Uses AsyncEngine instead of sync engine_from_config
- Reads DATABASE_URL from app settings (not alembic.ini)
- Imports Base + all models so autogenerate detects schema changes
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.engine import Connection

from alembic import context

# ── Import your app's Base and settings ──────────────────────────────────────
# Importing Base triggers the model imports in base.py (User, RefreshToken),
# which is what allows autogenerate to detect your tables.
from app.core.config import settings
from app.db.base import Base  # noqa: F401 — also imports all models

# ── Alembic Config ────────────────────────────────────────────────────────────
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from alembic.ini with the value from your .env
# This means you only need to update DATABASE_URL in one place
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# ── Offline mode ──────────────────────────────────────────────────────────────
# Generates SQL scripts without connecting to the DB
# Useful for reviewing migrations before applying them

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# ── Online mode ───────────────────────────────────────────────────────────────
# Connects to the DB and applies migrations directly

def do_run_migrations(connection: Connection) -> None:
    
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        # run_sync lets us use the synchronous Alembic API over an async connection
        await connection.run_sync(do_run_migrations)
 
    await connectable.dispose()
 
 
def run_migrations_online() -> None:
    """Entry point for online migrations — runs the async function via asyncio."""
    asyncio.run(run_async_migrations())

 
# ── Entry point ───────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
