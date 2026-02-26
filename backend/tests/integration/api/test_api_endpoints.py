"""
Integration tests for API endpoints.

Tests:
- Health check endpoints
- Game endpoints
- Game workflows
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Health check endpoint integration tests."""
    
    @pytest.mark.asyncio
    async def test_health_liveness_check(self, client_with_db: AsyncClient):
        """Test liveness probe returns healthy."""
        response = await client_with_db.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data["details"]
    
    @pytest.mark.asyncio
    async def test_health_readiness_check(self, client_with_db: AsyncClient):
        """Test readiness probe returns healthy."""
        response = await client_with_db.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["details"]["database"] == "connected"
    
    @pytest.mark.asyncio
    async def test_health_global_check(self, client_with_db: AsyncClient):
        """Test global health endpoint."""
        response = await client_with_db.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data["details"]
        assert "uptime_seconds" in data["details"]


@pytest.mark.integration
class TestGameEndpoints:
    """Game endpoint integration tests."""
    
    async def _create_authenticated_user(
        self,
        client: AsyncClient,
        username: str,
        password: str = "GamePass123!"
    ) -> str:
        """Helper to create user and return token."""
        # Register
        await client.post(
            "/users/register",
            json={"username": username, "password": password}
        )
        
        # Login
        login_response = await client.post(
            "/users/login",
            data={"username": username, "password": password}
        )
        
        return login_response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_create_game(self, client_with_db: AsyncClient):
        """Test creating a new game."""
        token = await self._create_authenticated_user(
            client_with_db,
            "game_creator_user"
        )
        
        response = await client_with_db.post(
            "/games/create_game",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["player1"] is not None
        assert data["player2"] is None
        assert data["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_create_game_requires_auth(self, client_with_db: AsyncClient):
        """Test creating game without authentication fails."""
        response = await client_with_db.post("/games/create_game")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestGameFlow:
    """Complete game workflow integration tests."""
    
    async def _create_authenticated_user(
        self,
        client: AsyncClient,
        username: str,
        password: str = "GamePass123!"
    ) -> str:
        """Helper to create user and return token."""
        await client.post(
            "/users/register",
            json={"username": username, "password": password}
        )
        
        login_response = await client.post(
            "/users/login",
            data={"username": username, "password": password}
        )
        
        return login_response.json()["access_token"]
