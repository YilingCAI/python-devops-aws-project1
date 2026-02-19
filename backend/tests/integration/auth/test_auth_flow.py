"""
Integration tests for authentication flows.

Tests complete authentication workflows:
- User registration
- User login
- Token generation
- Protected endpoints access
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAuthenticationFlow:
    """Complete authentication workflow tests."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client_with_db: AsyncClient):
        """Test successful user registration."""
        response = await client_with_db.post(
            "/users/register",
            json={
                "username": "newuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data  # Password must not be returned
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client_with_db: AsyncClient):
        """Test registration fails with duplicate username."""
        username = "duplicate_test_user"
        
        # Register first user
        response1 = await client_with_db.post(
            "/users/register",
            json={"username": username, "password": "Password123!"}
        )
        assert response1.status_code == 201
        
        # Try to register with same username
        response2 = await client_with_db.post(
            "/users/register",
            json={"username": username, "password": "DifferentPass123!"}
        )
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, client_with_db: AsyncClient):
        """Test successful login."""
        username = "login_test_user"
        password = "LoginPass123!"
        
        # Register user
        await client_with_db.post(
            "/users/register",
            json={"username": username, "password": password}
        )
        
        # Login
        response = await client_with_db.post(
            "/users/login",
            data={"username": username, "password": password}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client_with_db: AsyncClient):
        """Test login fails with invalid password."""
        username = "invalid_cred_user"
        
        # Register user
        await client_with_db.post(
            "/users/register",
            json={"username": username, "password": "CorrectPass123!"}
        )
        
        # Login with wrong password
        response = await client_with_db.post(
            "/users/login",
            data={"username": username, "password": "WrongPass123!"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_token(
        self,
        client_with_db: AsyncClient
    ):
        """Test accessing protected endpoint with valid token."""
        username = "protected_test_user"
        password = "ProtectedPass123!"
        
        # Register user
        await client_with_db.post(
            "/users/register",
            json={"username": username, "password": password}
        )
        
        # Login to get token
        login_response = await client_with_db.post(
            "/users/login",
            data={"username": username, "password": password}
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = await client_with_db.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == username

    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_invalid_token(
        self,
        client_with_db: AsyncClient
    ):
        """Test accessing protected endpoint with invalid token."""
        response = await client_with_db.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
