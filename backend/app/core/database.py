"""Database engine and session management for the application (restricted role)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.app_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency: yield a DB session, close on exit."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
