from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create a base class for declarative class definitions
Base = declarative_base()

def get_db():
    """
    Dependency function to get DB session.
    Handles session creation and teardown automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
