"""
Root conftest.py - Central pytest configuration and fixtures.

Imports fixtures from dedicated modules:
- tests/fixtures/db.py: Database session management with rollback
- tests/fixtures/client.py: AsyncClient with DB overrides
- tests/fixtures/auth.py: Authentication helpers and tokens
- tests/fixtures/settings.py: Test configuration
"""

import pytest
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root (/app) is on sys.path so `import app` works under pytest
ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)
# Also ensure the canonical `/app` path is present (runtime mount)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

# Load test environment variables before any app imports
# Priority: config/.env.test (test-specific) -> config/.env.local (local overrides)
test_env_files = [
    Path(__file__).parent.parent.parent / "config" / ".env.test",
    Path(__file__).parent.parent.parent / "config" / ".env.local",
]
for env_path in test_env_files:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded test environment from {env_path}")
    else:
        print(f"⚠ {env_path} not found, skipping")

# Import all fixtures
from tests.fixtures.db import test_engine, db_session
from tests.fixtures.client import (
    override_get_db,
    client_with_db
)
from tests.fixtures.auth import (
    test_user_data,
    created_user,
    user_token,
    authenticated_client,
)
from tests.fixtures.settings import get_test_database_url, get_test_jwt_secret


# Aliases for backward compatibility with existing tests
@pytest.fixture
def db(db_session):
    """Alias for db_session (with rollback)."""
    return db_session


@pytest.fixture
async def client(client_with_db):
    """Alias for client_with_db (AsyncClient with rollback DB)."""
    return client_with_db