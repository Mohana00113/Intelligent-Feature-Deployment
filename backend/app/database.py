from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./feature_flags.db"

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured. Add it to the backend environment file.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _run_migrations() -> None:
    """Apply Alembic migrations if the project migration configuration is present."""

    project_root = Path(__file__).resolve().parent.parent
    alembic_ini = project_root / "alembic.ini"
    migration_dir = project_root / "migrations"
    if not alembic_ini.exists() or not migration_dir.exists():
        return

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(migration_dir))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(config, "head")


def _seed_default_environments() -> None:
    """Insert the required default environment records without duplicating existing values."""

    from app.models import Environment

    with SessionLocal() as session:
        existing_keys = {item.key for item in session.query(Environment.key).all()}
        seed_values = [
            ("Development", "development", "Development environment"),
            ("Staging", "staging", "Staging environment"),
            ("Production", "production", "Production environment"),
        ]
        for name, key, description in seed_values:
            if key not in existing_keys:
                session.add(Environment(name=name, key=key, description=description))
        session.commit()


def init_db() -> None:
    """Create the SQLite schema if it does not exist before serving requests."""

    from app.models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)
    _run_migrations()
    _seed_default_environments()


def get_db():
    """Yield a SQLAlchemy database session for FastAPI dependency injection.

    The session is opened per request and closed automatically when the request
    completes, which keeps the API clean and avoids leaking database
    connections.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
