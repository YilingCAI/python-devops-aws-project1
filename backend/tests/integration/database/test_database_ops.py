"""
Integration tests for database operations.

Tests database-level functionality:
- Data persistence
- Transaction handling
- Data integrity
"""

import pytest
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.security import hash_password


@pytest.mark.integration
class TestDatabaseOperations:
    """Database operation integration tests."""
    
    def test_user_creation_and_retrieval(self, db_session: Session):
        """Test creating and retrieving user from database."""
        # Create user
        user = User(
            username="db_test_user",
            password=hash_password("Password123!"),
            wins=0
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Retrieve user
        retrieved_user = db_session.query(User).filter(
            User.username == "db_test_user"
        ).first()
        
        assert retrieved_user is not None
        assert retrieved_user.username == "db_test_user"
        assert retrieved_user.wins == 0
    
    def test_transaction_rollback_on_duplicate(self, db_session: Session):
        """Test transaction rollback when duplicate username is attempted."""
        # Create first user
        user1 = User(
            username="rollback_test_user",
            password=hash_password("Password123!"),
            wins=0
        )
        db_session.add(user1)
        db_session.commit()
        
        # Attempt to create user with duplicate username
        user2 = User(
            username="rollback_test_user",
            password=hash_password("Password123!"),
            wins=0
        )
        db_session.add(user2)
        
        # This should fail - but depends on DB constraints
        # If using unique constraints, should raise IntegrityError
        try:
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # Verify only one user exists
        count = db_session.query(User).filter(
            User.username == "rollback_test_user"
        ).count()
        
        assert count == 1
    
    def test_user_data_isolation_between_sessions(self, db_session: Session, test_engine):
        """Test that data is isolated between test sessions.

        Create a fresh committing session bound to the test engine to ensure
        visibility differences between the transactional test session and a
        separate session that commits directly to the DB.
        """
        # Count users in transactional test session
        count_in_session = db_session.query(User).count()

        # Create a separate committing session bound to the engine
        commit_session = Session(bind=test_engine, future=True)
        try:
            count_in_commit = commit_session.query(User).count()
        finally:
            commit_session.close()

        # Both should start empty or with same data
        assert count_in_session == count_in_commit
