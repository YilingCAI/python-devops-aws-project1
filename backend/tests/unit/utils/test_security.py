"""
Unit tests for security utilities.

Tests:
- Password hashing and verification
- JWT token creation and validation
- No database or network calls
"""

import pytest
from datetime import datetime, timedelta
from app.core.security import hash_password, verify_password, create_access_token


@pytest.mark.unit
class TestPasswordSecurity:
    """Password hashing and verification tests."""
    
    def test_hash_password_returns_different_hash_each_time(self):
        """Test password hashing returns different values (salt)."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification succeeds with correct password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Test password verification fails with incorrect password."""
        password = "OriginalPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False
    
    def test_verify_password_case_sensitive(self):
        """Test password verification is case-sensitive."""
        password = "TestPassword123!"
        wrong_case = "testpassword123!"
        hashed = hash_password(password)
        
        result = verify_password(wrong_case, hashed)
        assert result is False


@pytest.mark.unit
class TestJWTTokens:
    """JWT token creation and validation tests."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = "user123"
        token = create_access_token({"sub": user_id})
        
        # Token should be string with 3 parts (header.payload.signature)
        assert isinstance(token, str)
        assert token.count(".") == 2
    
    def test_create_access_token_with_custom_expires(self):
        """Test JWT token creation with custom expiration."""
        user_id = "user456"
        expires_delta = timedelta(hours=2)
        token = create_access_token(
            {"sub": user_id},
            expires_delta=expires_delta
        )
        
        assert isinstance(token, str)
        assert token.count(".") == 2
    
    def test_different_payloads_create_different_tokens(self):
        """Test different payloads create different tokens."""
        token1 = create_access_token({"sub": "user1"})
        token2 = create_access_token({"sub": "user2"})
        
        assert token1 != token2
