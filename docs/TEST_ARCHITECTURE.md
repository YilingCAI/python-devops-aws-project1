# Test Architecture

Testing strategy for the FastAPI backend. Covers test types, fixture design, database isolation, and how tests run in CI.

---

## Overview

```
tests/
├── unit/           ← Fast, fully mocked — no database, no network, no docker required
│   ├── services/   ← Business logic tests (user_service, game_service)
│   └── core/       ← Utility tests (security, config)
│
└── integration/    ← Real database — auto-rollback per test
    ├── api/        ← Full HTTP request/response cycle tests
    └── db/         ← Repository and data persistence tests
```

### Test layer responsibilities

| Layer | DB | Network | Speed | When to write |
|---|---|---|---|---|
| Unit | ❌ mocked | ❌ mocked | ~10ms/test | All business logic, utilities |
| Integration | ✅ real | ✅ real HTTP | ~100ms/test | API endpoints, DB queries |

---

## Running Tests

```bash
cd backend

# All tests
poetry run pytest

# Unit tests only (fast, no DB)
poetry run pytest tests/unit -m unit -v

# Integration tests only (requires running postgres)
poetry run pytest tests/integration -m integration -v

# Single test
poetry run pytest tests/unit/services/test_user_service.py::TestUserRegistration::test_register_success -v

# With coverage
poetry run pytest --cov=app --cov-report=html --cov-report=term-missing
open htmlcov/index.html

# Stop on first failure
poetry run pytest -x

# Show local variables on failure
poetry run pytest -l

# Parallelise (install pytest-xdist first)
poetry run pytest -n auto
```

---

## Pytest Markers

Defined in `pytest.ini`:

```ini
[pytest]
markers =
    unit: mark test as a unit test (no database, no network)
    integration: mark test as an integration test (requires database)
```

Usage:
```python
import pytest

@pytest.mark.unit
def test_password_hash_is_not_plaintext():
    hashed = hash_password("secret123")
    assert hashed != "secret123"

@pytest.mark.integration
async def test_create_user_persists_to_db(db_session):
    user = await create_user(db_session, email="a@b.com", password="pass")
    result = await db_session.get(User, user.id)
    assert result.email == "a@b.com"
```

---

## Fixture Reference

All fixtures are defined in `tests/conftest.py`.

### Database fixtures

```python
@pytest.fixture(scope="session")
def test_engine():
    """Single SQLAlchemy engine for the entire test session.
    Points to the test database (DATABASE_NAME=testdb from config/.env.test).
    Creates all tables on setup, drops them after all tests complete.
    """

@pytest.fixture(scope="function")
async def db_session(test_engine):
    """Per-test transactional session.
    Wraps each test in a transaction that is ROLLED BACK when the test ends,
    leaving the database in a clean state for the next test.
    No teardown logic needed in individual tests.
    """

@pytest.fixture(scope="function")
async def db_session_with_commit(test_engine):
    """Use when the test must commit (e.g. testing cascade deletes).
    Truncates all tables after the test instead of rolling back.
    """
```

### HTTP client fixtures

```python
@pytest.fixture
async def client(db_session):
    """AsyncClient pointing at the full FastAPI app.
    Injects db_session via dependency override — same session as the test,
    so the test can verify DB state without committing.
    """

@pytest.fixture
async def client_with_commit(db_session_with_commit):
    """AsyncClient with a session that commits.
    Use for tests that check persistent side effects.
    """
```

### Authentication fixtures

```python
@pytest.fixture
def test_user_data():
    """Pre-defined user credentials dict.
    Returns: {"email": "test@example.com", "password": "TestPassword1!"}
    """

@pytest.fixture
async def created_user(db_session, test_user_data):
    """Creates a real User row in the DB.
    Rolled back after the test (via db_session).
    """

@pytest.fixture
async def user_token(created_user):
    """Returns a valid JWT access token for created_user."""

@pytest.fixture
async def authenticated_client(client, user_token):
    """AsyncClient with Authorization: Bearer <token> pre-set.
    Use for tests that require an authenticated user.
    """
```

---

## Writing Unit Tests

Unit tests mock all I/O. Never import database models or make network calls.

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import register_user, UserAlreadyExistsError

@pytest.mark.unit
class TestUserRegistration:

    async def test_register_success(self):
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None   # user doesn't exist yet
        mock_repo.create.return_value = MagicMock(id=1, email="new@example.com")

        # Act
        result = await register_user(
            repo=mock_repo,
            email="new@example.com",
            password="StrongPass1!"
        )

        # Assert
        assert result.email == "new@example.com"
        mock_repo.create.assert_called_once()

    async def test_register_duplicate_email_raises(self):
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = MagicMock()  # user already exists

        # Act + Assert
        with pytest.raises(UserAlreadyExistsError):
            await register_user(
                repo=mock_repo,
                email="existing@example.com",
                password="StrongPass1!"
            )
```

---

## Writing Integration Tests

Integration tests exercise the full stack: HTTP request → FastAPI router → service → database → response.

```python
# tests/integration/api/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthEndpoints:

    async def test_register_and_login(self, client: AsyncClient):
        # Register
        resp = await client.post("/auth/register", json={
            "email": "integration@example.com",
            "password": "StrongPass1!"
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "integration@example.com"

        # Login with same credentials
        resp = await client.post("/auth/login", json={
            "email": "integration@example.com",
            "password": "StrongPass1!"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_protected_route_requires_token(self, client: AsyncClient):
        resp = await client.get("/users/me")
        assert resp.status_code == 401

    async def test_protected_route_with_valid_token(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.get("/users/me")
        assert resp.status_code == 200
        assert "email" in resp.json()
```

---

## Database Isolation Strategy

Each integration test runs inside a database transaction that is **rolled back** when the test ends. This means:

- Tests are completely isolated — order doesn't matter
- No cleanup code required in individual tests
- The DB is always in a clean state
- Tests run at the same speed as real DB operations (they use real SQL)

How it works internally:

```python
@pytest.fixture(scope="function")
async def db_session(test_engine):
    async with test_engine.connect() as conn:
        await conn.begin()                          # start outer transaction
        async with AsyncSession(bind=conn) as session:
            await session.begin_nested()            # savepoint
            yield session                           # test runs here
            await session.rollback()               # rollback savepoint
        await conn.rollback()                      # rollback outer transaction
```

The FastAPI `get_db()` dependency is overridden to use this same session:

```python
app.dependency_overrides[get_db] = lambda: db_session
```

---

## CI Configuration

Tests run in `ci.yml` with a real PostgreSQL service container:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER:     ${{ env.POSTGRES_USER }}
      POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
      POSTGRES_DB:       ${{ env.POSTGRES_DB }}
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - ${{ env.POSTGRES_PORT }}:5432
```

The credentials match `config/.env.test` — the same file used locally. This means tests behave identically locally and in CI.

Unit and integration tests run as separate steps so they can be distinguished in the CI summary:

```yaml
- name: Unit tests
  run: pytest tests/unit -m unit -v --junitxml=test-results-unit.xml

- name: Integration tests
  run: pytest tests/integration -m integration -v --junitxml=test-results-integration.xml
```

Coverage is uploaded to Codecov after the integration test step.
