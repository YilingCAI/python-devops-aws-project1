from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# SQLAlchemy 2.0 / "future" style engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Session factory (SQLAlchemy 2.0 style)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

# Declarative base
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a SQLAlchemy Session (2.0 style)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
