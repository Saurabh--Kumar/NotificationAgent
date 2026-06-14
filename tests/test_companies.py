import uuid
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus


def test_get_companies_returns_distinct_companies(client, db: Session, test_company_id):
    response = client.get("/api/v1/companies")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(company["id"] == test_company_id for company in data)
    assert all("name" in company for company in data)


def test_get_campaigns_by_company_returns_active_campaigns(
    client, db: Session, test_company_id, test_campaign_id
):
    # Add another active campaign
    active_campaign = Campaign(
        id=uuid.uuid4(),
        company_id=uuid.UUID(test_company_id),
        company_name="Test Company",
        name="Active Campaign 2",
        description="Another active campaign",
        theme="Test Theme 2",
        category="Test Category 2",
        brand_voice="Friendly",
        target_audience="Young adults",
        industry="Technology",
        status=CampaignStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
    )
    db.add(active_campaign)
    db.commit()

    response = client.get(f"/api/v1/companies/{test_company_id}/campaigns")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(campaign["status"] == "ACTIVE" for campaign in data)
    assert all(campaign["company_id"] == test_company_id for campaign in data)


def test_get_campaigns_by_company_wrong_company_id_returns_empty(
    client, test_company_id
):
    wrong_company_id = "99999999-9999-9999-9999-999999999999"

    response = client.get(f"/api/v1/companies/{wrong_company_id}/campaigns")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == []


def test_get_campaigns_by_company_filters_inactive_campaigns(
    client, db: Session, test_company_id
):
    # Add an inactive campaign
    inactive_campaign = Campaign(
        id=uuid.uuid4(),
        company_id=uuid.UUID(test_company_id),
        company_name="Test Company",
        name="Inactive Campaign",
        description="Should not appear",
        theme="Test Theme",
        category="Test Category",
        brand_voice="Friendly",
        target_audience="Young adults",
        industry="Technology",
        status=CampaignStatus.DRAFT,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
    )
    db.add(inactive_campaign)
    db.commit()

    response = client.get(f"/api/v1/companies/{test_company_id}/campaigns")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(campaign["status"] == "ACTIVE" for campaign in data)
    assert all(campaign["name"] != "Inactive Campaign" for campaign in data)
