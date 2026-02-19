"""Test settings and configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables from centralized config folder
# Priority: config/.env.test (test-specific) -> config/.env.local (local overrides)
test_env_files = [
    Path(__file__).parent.parent.parent.parent / "config" / ".env.test",
    Path(__file__).parent.parent.parent.parent / "config" / ".env.local",
]
for env_path in test_env_files:
    if env_path.exists():
        load_dotenv(env_path, override=True)


def get_test_database_url() -> str:
    """
    Get test database URL from environment.
    
    Returns:
        str: PostgreSQL connection string
    """
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "test_myproject")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_test_jwt_secret() -> str:
    """
    Get JWT secret for testing.
    
    Returns:
        str: JWT secret key
    """
    return os.getenv("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")
