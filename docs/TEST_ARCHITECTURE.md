# Test Suite Architecture - Complete Reference

## 📚 Quick Start

```bash
# Run all tests
pytest

# Run only unit tests (fast, no DB)
pytest -m unit

# Run only integration tests (needs DB)
pytest -m integration

# Run specific test
pytest tests/unit/services/test_user_service.py::TestUserRegistration::test_register_success

# Run with coverage
pytest --cov=app --cov-report=html
```

## 🏗️ Architecture Overview

### Test Layer Organization

```
┌─────────────────────────────────────┐
│      Unit Tests (@pytest.mark.unit) │  ← Mock everything
│  - Services (business logic)        │  ← No database
│  - Utils (security, helpers)        │  ← No network calls
│  - Repositories (data access)       │  ← 100% mocked
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ Integration Tests (@pytest.mark...)  │  ← Real database
│  - API endpoints (full requests)    │  ← Real HTTP with AsyncClient
│  - Auth workflows (complete flows)  │  ← Complete workflows
│  - Database ops (data persistence)  │  ← Auto-rollback after each test
└─────────────────────────────────────┘
```

### Fixture Hierarchy

```
conftest.py (root configuration)
├── fixtures/db.py
│   ├── test_engine (session scope) - Single DB engine
│   ├── db_session (function scope) - Transactional rollback
│   └── db_session_with_commit - Manual cleanup
├── fixtures/client.py
│   ├── override_get_db - Dependency injector
│   ├── client_with_db - AsyncClient + rollback
│   └── client_with_commit_db - AsyncClient + commit
├── fixtures/auth.py
│   ├── test_user_data - Pre-configured credentials
│   ├── created_user - User in database
│   ├── user_token - Valid JWT token
│   └── authenticated_client - Client with auth header
└── fixtures/settings.py
    ├── get_test_database_url() - Test DB URL
    └── get_test_jwt_secret() - JWT secret
```

## 📂 File Structure

```
backend/
├── pytest.ini                    # Pytest configuration
├── .env.test                     # Test environment variables
├── validate_tests.py             # Validation script
│
├── tests/
│   ├── conftest.py              # Root fixtures (imports from below)
│   ├── __init__.py
│   │
│   ├── fixtures/                # Reusable fixtures
│   │   ├── __init__.py
│   │   ├── settings.py          # Config loader
│   │   ├── db.py                # Database sessions
│   │   ├── client.py            # HTTP client setup
│   │   └── auth.py              # Auth helpers
│   │
│   ├── unit/                    # Unit tests (mocked)
│   │   ├── __init__.py
│   │   ├── services/            # Business logic tests
│   │   │   ├── __init__.py
│   │   │   └── test_user_service.py
│   │   ├── repositories/        # Data access tests
│   │   │   └── __init__.py
│   │   └── utils/               # Utility tests
│   │       ├── __init__.py
│   │       └── test_security.py
│   │
│   ├── integration/             # Integration tests (real DB)
│   │   ├── __init__.py
│   │   ├── api/                 # HTTP endpoint tests
│   │   │   ├── __init__.py
│   │   │   └── test_api_endpoints.py
│   │   ├── auth/                # Auth workflow tests
│   │   │   ├── __init__.py
│   │   │   └── test_auth_flow.py
│   │   └── database/            # Database tests
│   │       ├── __init__.py
│   │       └── test_database_ops.py
│   │
│   └── [OLD TESTS - can archive]
│       ├── test_users.py
│       ├── test_auth_flow.py
│       ├── test_health.py
│       ├── test_game.py
│       ├── test_game_flow.py
│       └── test_api_flow.py
│
└── app/
    ├── core/
    │   ├── logging.py            # pythonjsonlogger configured here
    │   ├── config.py
    │   └── security.py
    ├── api/
    ├── models/
    └── db/
```

## 🔌 Configuration Files

### `.env.test` - Test Environment

```env
ENVIRONMENT=testing
DEBUG=True
DATABASE_NAME=test_myproject
JWT_SECRET_KEY=test-secret-key-...
LOG_FORMAT=text
```

**Key Points**:
- Separate test database
- Test-specific secrets
- Debug mode enabled
- No hardcoded values in tests

### `pytest.ini` - Pytest Configuration

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    asyncio: Async tests
```

**Key Points**:
- `asyncio_mode = auto` - Enable async support
- `testpaths = tests` - Only run tests in tests/ directory
- Markers for test filtering

### `conftest.py` - Fixture Management

```python
# Loads .env.test automatically
load_dotenv(env_path, override=True)

# Imports all fixtures from dedicated modules
from tests.fixtures.db import test_engine, db_session
from tests.fixtures.client import client_with_db
from tests.fixtures.auth import authenticated_client
```

**Key Points**:
- Central fixture configuration
- Automatic environment setup
- Backward-compatible aliases (db, client)

## 🧪 Writing Tests

### Unit Test Pattern

```python
import pytest
from unittest.mock import MagicMock

@pytest.mark.unit
class TestUserService:
    """Business logic tests - mocked database."""
    
    def test_register_success(self):
        # Setup - Mock everything external
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute - Test business logic
        user_in = UserCreate(username="alice", password="Pass123!")
        result = users.register(user_in, db=mock_db)
        
        # Assert - Verify behavior
        assert result.username == "alice"
        mock_db.add.assert_called_once()
```

### Integration Test Pattern

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthFlow:
    """Complete workflows - real database."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client_with_commit_db: AsyncClient):
        # Register
        await client_with_commit_db.post(
            "/users/register",
            json={"username": "testuser", "password": "Pass123!"}
        )
        
        # Login
        response = await client_with_commit_db.post(
            "/users/login",
            data={"username": "testuser", "password": "Pass123!"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "access_token" in response.json()
```

## 🔄 Database Transaction Flow

### Per-Test Isolation (Automatic Rollback)

```python
@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()      # Start transaction
    
    session = sessionmaker(bind=connection)(class_=Session)
    yield session                         # Run test
    
    transaction.rollback()                # Undo all changes
    connection.close()
```

**Flow for Each Test**:
1. Test starts with fresh database state
2. Test makes database changes
3. Test ends
4. Transaction rolls back - undo all changes
5. Next test gets fresh state again

**Benefits**:
- ✅ Zero test pollution
- ✅ No cleanup code needed
- ✅ Ultra-fast (no DROP statements)
- ✅ 100% reliable

## 🔐 Fixture Dependencies

### Simple Fixture Usage

```python
def test_something(db_session: Session):
    """Fixture injected automatically."""
    user = db_session.query(User).first()
    assert user is not None
```

### Chained Fixtures

```python
@pytest.fixture
async def created_user(db_session, test_user_data):
    # Depends on db_session and test_user_data
    user = User(
        username=test_user_data["username"],
        password=hash_password(test_user_data["password"])
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
async def user_token(created_user):
    # Depends on created_user
    return create_access_token({"sub": str(created_user.id)})

def test_something(user_token: str):
    # Test gets token automatically via dependency chain
    assert user_token.count(".") == 2
```

## 🎯 Test Markers

### Run by Marker

```bash
# Only fast unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Only async tests
pytest -m asyncio

# Exclude slow tests
pytest -m "not slow"

# Unit tests OR async (not integration)
pytest -m "unit or asyncio"
```

### Using Markers

```python
@pytest.mark.unit
class TestFast:
    pass

@pytest.mark.integration
class TestComplete:
    pass

@pytest.mark.asyncio
async def test_async():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

## 📊 Example Test Results

```
======================== test session starts ==========================
collected 25 items

tests/unit/services/test_user_service.py::TestUserRegistration::test_register_success PASSED
tests/unit/services/test_user_service.py::TestUserRegistration::test_register_duplicate_username PASSED
tests/unit/services/test_user_service.py::TestUserLogin::test_login_success PASSED
tests/unit/utils/test_security.py::TestPasswordSecurity::test_hash_password PASSED
tests/integration/auth/test_auth_flow.py::TestAuthenticationFlow::test_register_user_success PASSED
tests/integration/api/test_api_endpoints.py::TestHealthEndpoints::test_health_liveness_check PASSED
tests/integration/database/test_database_ops.py::TestDatabaseOperations::test_user_creation PASSED

=================== 25 passed in 12.34s =========================
```

## 🚨 Common Issues & Solutions

### Issue: "Test database not found"
**Solution**: 
```bash
createdb test_myproject
```

### Issue: "asyncio_mode auto not recognized"
**Solution**: 
```bash
pip install pytest-asyncio>=1.3.0
```

### Issue: "pythonjsonlogger import error"
**Solution**: Already installed! Version 2.0.7 in your environment.

### Issue: "Database constraint errors"
**Solution**: Use unique test data
```python
def test_something(self):
    username = f"test_user_{uuid4()}"  # Unique each time
```

### Issue: "Tests fail in CI but pass locally"
**Solution**: Ensure test database exists in CI:
```bash
createdb test_myproject || true
```

## 🎓 Best Practices

### ✅ Always

- ✅ Use `@pytest.mark.unit` or `@pytest.mark.integration`
- ✅ Use fixtures instead of manual setup
- ✅ Use `db_session` for auto-rollback
- ✅ Use `AsyncClient` for HTTP tests
- ✅ Use descriptive test names
- ✅ Load config from `.env.test`
- ✅ Test complete workflows in integration tests
- ✅ Separate business logic tests from HTTP tests

### ❌ Never

- ❌ Mock database in integration tests
- ❌ Test routers in unit tests
- ❌ Use `TestClient` (use `AsyncClient`)
- ❌ Hardcode test data or URLs
- ❌ Skip cleanup (fixtures handle it)
- ❌ Mix unit and integration concerns
- ❌ Test without markers
- ❌ Create test data that isn't cleaned up

## 📈 Performance Tips

1. **Run unit tests first** (fast feedback):
   ```bash
   pytest -m unit
   ```

2. **Use parallel execution**:
   ```bash
   pip install pytest-xdist
   pytest -n auto
   ```

3. **Run only changed tests**:
   ```bash
   pytest --lf  # last failed
   pytest --ff  # failed first
   ```

4. **Generate coverage report** (sparse):
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

## 🔗 Related Documentation

- **Full Guide**: `docs/TEST_REFACTOR_GUIDE.md`
- **Refactor Summary**: `TESTING_REFACTOR_SUMMARY.md`
- **pytest Docs**: https://docs.pytest.org/
- **AsyncClient**: https://www.python-httpx.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/

## ✨ Next Steps

1. Create test database: `createdb test_myproject`
2. Run unit tests: `pytest -m unit` (no DB needed)
3. Run all tests: `pytest` (requires test DB)
4. Check coverage: `pytest --cov=app`
5. Add new tests following the patterns above

---

**Your test suite is now production-ready with enterprise-grade architecture!** 🚀
