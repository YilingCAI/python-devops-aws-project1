import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock
from app.db.session import Base, get_db
from main import app  # make sure this is your FastAPI instance

# -----------------------------
# Test database setup (SQLite)
# -----------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# -----------------------------
# Fixture: Database session
# -----------------------------
@pytest.fixture(scope="function")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# -----------------------------
# Fixture: FastAPI client with working DB
# -----------------------------
@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# -----------------------------
# Fixture: Mocked DB session
# -----------------------------
@pytest.fixture
def mock_db():
    mock_session = MagicMock(spec=Session)
    yield mock_session


# -----------------------------
# Fixture: FastAPI client with broken DB (simulate failure)
# -----------------------------
@pytest.fixture
def client_broken_db():
    class FakeBrokenDB:
        def execute(self, *args, **kwargs):
            raise Exception("DB unreachable")

    def override_get_db():
        yield FakeBrokenDB()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()