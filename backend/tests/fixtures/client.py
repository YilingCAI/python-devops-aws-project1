"""HTTP client fixtures for tests using ASGI transport and lifespan manager."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from asgi_lifespan import LifespanManager
from main import app
from app.db.session import get_db


@pytest.fixture
def override_get_db(db_session: Session):
    """Override FastAPI dependency to use test database session."""
    def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
async def client_with_db(db_session: Session, override_get_db):
    """Create `AsyncClient` that talks to the ASGI app via ASGITransport.

    Uses `LifespanManager` to run application startup/shutdown and
    `ASGITransport` so the client makes in-process ASGI calls without
    passing `app=` directly to `AsyncClient`.
    """
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    # Ensure app startup/shutdown events run
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()
