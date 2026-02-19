"""Database fixtures for tests, SQLAlchemy 2.0 style."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from tests.fixtures.settings import get_test_database_url
from app.db.session import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create a SQLAlchemy Engine for the test session."""
    engine = create_engine(
        get_test_database_url(),
        future=True,
        pool_pre_ping=True,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop tables and dispose
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide a SQLAlchemy `Session` bounded to a SAVEPOINTed transaction.

    Each test runs inside a nested transaction (SAVEPOINT) so tests can
    call `commit()` safely and still be rolled back at teardown.
    """
    # Connect and begin a top-level transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Bind a Session to the connection
    session = Session(bind=connection, future=True)

    # start a nested transaction (SAVEPOINT)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        # If the nested transaction ended, reopen it for test isolation
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Teardown: close session and rollback outer transaction
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_session_with_commit(test_engine):
    """Provide a real session that commits to the test database.

    This fixture is suitable for tests that need to verify data persisted
    across sessions. It cleans up by deleting rows after the test.
    """
    session = Session(bind=test_engine, future=True)

    yield session

    # Cleanup: delete all data created during the test
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()