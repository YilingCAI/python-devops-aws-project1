"""Authentication fixtures for tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.security import hash_password, create_access_token


@pytest.fixture
async def test_user_data():
    """
    Provide test user credentials.
    
    Returns:
        dict: User credentials for testing
    """
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com"
    }


@pytest.fixture
async def created_user(db_session: Session, test_user_data: dict):
    """
    Create a test user in the database.
    
    Args:
        db_session: Database session
        test_user_data: User credentials
        
    Returns:
        User: Created user object
    """
    user = User(
        username=test_user_data["username"],
        password=hash_password(test_user_data["password"]),
        wins=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
async def user_token(created_user: User):
    """
    Generate JWT token for created test user.
    
    Args:
        created_user: Created user object
        
    Returns:
        str: JWT access token
    """
    return create_access_token({"sub": str(created_user.id)})


@pytest.fixture
async def authenticated_client(client_with_db: AsyncClient, user_token: str):
    """
    Provide AsyncClient with authentication headers.
    
    Args:
        client_with_db: HTTP client with test database
        user_token: JWT token
        
    Returns:
        AsyncClient: Client with authorization header
    """
    client_with_db.headers["Authorization"] = f"Bearer {user_token}"
    return client_with_db
