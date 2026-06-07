#!/usr/bin/env python3
"""
Database setup script for Notification Agent.
Creates the database, tables, and inserts dummy campaigns.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
import uuid

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.session import Base, engine
from app.models.campaign import Campaign
from app.models.notification_session import NotificationSession
from app.models.enums import CampaignStatus, NotificationSessionStatus
from sqlalchemy.orm import sessionmaker

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_database():
    """Create the database if it doesn't exist."""
    # Connect to postgres default database to create our database
    default_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
    
    default_engine = create_engine(default_url)
    
    with default_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'")
        )
        exists = result.scalar()
        
        if not exists:
            conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
            conn.commit()
            print(f"Database '{settings.POSTGRES_DB}' created successfully.")
        else:
            print(f"Database '{settings.POSTGRES_DB}' already exists.")
    
    default_engine.dispose()


def create_tables():
    """Create all tables using SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


def insert_dummy_campaigns():
    """Insert dummy campaigns into the database."""
    db = SessionLocal()
    
    try:
        # Check if campaigns already exist
        existing_count = db.query(Campaign).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing campaigns. Skipping dummy data insertion.")
            return
        
        # Generate some UUIDs for companies
        company_id_1 = uuid.uuid4()
        company_id_2 = uuid.uuid4()
        company_id_3 = uuid.uuid4()
        
        # Create dummy campaigns
        campaigns = [
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_1,
                company_name="TechCorp Solutions",
                brand_voice="Professional and innovative",
                target_audience="Enterprise software developers and IT managers",
                industry="Technology",
                name="Q2 Product Launch Campaign",
                description="Launch campaign for our new cloud-based project management tool targeting enterprise clients",
                theme="Product Launch",
                category="Marketing",
                status=CampaignStatus.ACTIVE,
                start_date=datetime.now(timezone.utc) - timedelta(days=30),
                end_date=datetime.now(timezone.utc) + timedelta(days=60),
            ),
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_1,
                company_name="TechCorp Solutions",
                brand_voice="Professional and innovative",
                target_audience="Enterprise software developers and IT managers",
                industry="Technology",
                name="Summer Developer Conference 2024",
                description="Annual developer conference showcasing the latest in cloud computing and DevOps",
                theme="Conference",
                category="Event",
                status=CampaignStatus.DRAFT,
                start_date=datetime.now(timezone.utc) + timedelta(days=90),
                end_date=datetime.now(timezone.utc) + timedelta(days=92),
            ),
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_2,
                company_name="EcoRetail Brands",
                brand_voice="Sustainable and customer-focused",
                target_audience="Eco-conscious consumers aged 25-45",
                industry="Retail",
                name="Green Friday Sale",
                description="Special sale event featuring sustainable products with up to 40% off",
                theme="Sales Event",
                category="Promotion",
                status=CampaignStatus.ACTIVE,
                start_date=datetime.now(timezone.utc) - timedelta(days=15),
                end_date=datetime.now(timezone.utc) + timedelta(days=15),
            ),
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_2,
                company_name="EcoRetail Brands",
                brand_voice="Sustainable and customer-focused",
                target_audience="Eco-conscious consumers aged 25-45",
                industry="Retail",
                name="Holiday Gift Guide",
                description="Curated selection of eco-friendly gifts for the holiday season",
                theme="Holiday",
                category="Marketing",
                status=CampaignStatus.PAUSED,
                start_date=datetime.now(timezone.utc) + timedelta(days=30),
                end_date=datetime.now(timezone.utc) + timedelta(days=60),
            ),
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_3,
                company_name="HealthFirst Medical",
                brand_voice="Trustworthy and caring",
                target_audience="Healthcare professionals and patients",
                industry="Healthcare",
                name="New Patient Portal Launch",
                description="Introducing our new patient portal for easier appointment scheduling and medical record access",
                theme="Product Launch",
                category="Healthcare",
                status=CampaignStatus.COMPLETED,
                start_date=datetime.now(timezone.utc) - timedelta(days=120),
                end_date=datetime.now(timezone.utc) - timedelta(days=30),
            ),
            Campaign(
                id=uuid.uuid4(),
                company_id=company_id_3,
                company_name="HealthFirst Medical",
                brand_voice="Trustworthy and caring",
                target_audience="Healthcare professionals and patients",
                industry="Healthcare",
                name="Annual Health Checkup Drive",
                description="Encouraging annual health checkups with special discounts for early bird bookings",
                theme="Health Awareness",
                category="Healthcare",
                status=CampaignStatus.CANCELLED,
                start_date=datetime.now(timezone.utc) - timedelta(days=60),
                end_date=datetime.now(timezone.utc) - timedelta(days=30),
            ),
        ]
        
        db.add_all(campaigns)
        db.commit()
        
        print(f"Inserted {len(campaigns)} dummy campaigns successfully.")
        
    finally:
        db.close()


def main():
    """Main function to set up the database."""
    print("Setting up Notification Agent database...")
    
    # Create database
    create_database()
    
    # Create tables
    create_tables()
    
    # Insert dummy campaigns
    insert_dummy_campaigns()
    
    print("\nDatabase setup complete!")


if __name__ == "__main__":
    main()