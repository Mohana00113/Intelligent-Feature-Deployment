from __future__ import annotations

import os

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


def init_db() -> None:
    """Create the SQLite schema if it does not exist before serving requests."""

    from app.models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)


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
