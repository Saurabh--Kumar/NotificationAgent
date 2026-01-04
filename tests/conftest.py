import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.main import app
from app.api.dependencies import get_db
from unittest.mock import Mock, patch

# Mock Celery task to avoid Redis dependency
import app.api.endpoints.notification_sessions as notification_sessions_module
notification_sessions_module.run_agent_task = Mock()
notification_sessions_module.run_agent_task.delay = Mock(return_value=Mock(id="test-task-id"))



# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override the get_db dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def init_db():
    """Initialize the database once for the module."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Insert a test campaign
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("""
                INSERT INTO campaigns 
                (id, company_id, name, description, theme, category, status, start_date, end_date, created_at, updated_at)
                VALUES 
                ('33333333-3333-3333-3333-333333333333', 
                    '11111111-1111-1111-1111-111111111111', 
                    'Test Campaign', 
                    'Test Description', 
                    'Test Theme', 
                    'Test Category', 
                    'DRAFT',
                    '2025-01-01 00:00:00',
                    '2025-12-31 23:59:59',
                    '2025-01-01 00:00:00',
                    '2025-01-01 00:00:00')
            """))
    
    yield
    
    # Drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    
    # Cleanup data created during test (since rollback might not work if commit was called)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("DELETE FROM notification_sessions"))



@pytest.fixture(scope="module")
def test_company_id():
    """Return a test company ID."""
    return "11111111-1111-1111-1111-111111111111"


@pytest.fixture(scope="module")
def test_admin_id():
    """Return a test admin ID."""
    return "22222222-2222-2222-2222-222222222222"


@pytest.fixture(scope="module")
def test_campaign_id():
    """Return a test campaign ID."""
    return "33333333-3333-3333-3333-333333333333"




@pytest.fixture(scope="module")

def client():
    """Create a TestClient instance."""
    with TestClient(app) as c:
        yield c