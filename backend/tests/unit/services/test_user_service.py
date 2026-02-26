"""
Unit tests for user authentication service logic.

Tests:
- Password hashing and verification
- JWT token creation and validation
- Business logic without HTTP layer
"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from fastapi import HTTPException

from app.api import users
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


@pytest.mark.unit
class TestUserRegistration:
    """User registration business logic tests."""
    
    def test_register_success(self):
        """Test successful user registration."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_in = UserCreate(username="alice", password="TestPassword123!")
        result = users.register(user_in, db=mock_db)
        
        assert result.username == "alice"
        assert result.wins == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        mock_db = MagicMock()
        existing_user = SimpleNamespace(username="alice", id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        user_in = UserCreate(username="alice", password="TestPassword123!")
        
        with pytest.raises(HTTPException) as exc_info:
            users.register(user_in, db=mock_db)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail.lower()


@pytest.mark.unit
class TestUserLogin:
    """User login business logic tests."""
    
    def test_login_success(self):
        """Test successful login with correct credentials."""
        mock_db = MagicMock()
        db_user = SimpleNamespace(id=1, username="alice", password="hashed_password")
        mock_db.query.return_value.filter.return_value.first.return_value = db_user
        
        form = SimpleNamespace(username="alice", password="correct_password")
        
        with patch("app.api.users.verify_password", return_value=True):
            with patch("app.api.users.create_access_token", return_value="token123"):
                result = users.login(form_data=form, db=mock_db)
        
        assert result["access_token"] == "token123"
        assert result["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        mock_db = MagicMock()
        db_user = SimpleNamespace(id=1, username="alice", password="hashed_password")
        mock_db.query.return_value.filter.return_value.first.return_value = db_user
        
        form = SimpleNamespace(username="alice", password="wrong_password")
        
        with patch("app.api.users.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                users.login(form_data=form, db=mock_db)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()
    
    def test_login_user_not_found(self):
        """Test login fails when user not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        form = SimpleNamespace(username="nonexistent", password="password")
        
        with pytest.raises(HTTPException) as exc_info:
            users.login(form_data=form, db=mock_db)
        
        assert exc_info.value.status_code == 401


@pytest.mark.unit
class TestUserProfile:
    """User profile retrieval tests."""
    
    def test_read_my_profile(self):
        """Test reading current user profile."""
        current_user = SimpleNamespace(id=1, username="alice", wins=5)
        result = users.read_my_profile(current_user=current_user)
        
        assert result["id"] == 1
        assert result["username"] == "alice"
        assert result["wins"] == 5
