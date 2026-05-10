from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate


def create_campaign(db: Session, campaign_in: CampaignCreate) -> Campaign:
    db_campaign = Campaign(
        company_id=campaign_in.company_id,
        company_name=campaign_in.company_name,
        name=campaign_in.name,
        description=campaign_in.description,
        theme=campaign_in.theme,
        category=campaign_in.category,
        brand_voice=campaign_in.brand_voice,
        target_audience=campaign_in.target_audience,
        industry=campaign_in.industry,
        start_date=campaign_in.start_date,
        end_date=campaign_in.end_date,
        status=CampaignStatus.DRAFT,
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def get_campaign(
    db: Session, campaign_id: UUID, company_id: Optional[UUID] = None
) -> Optional[Campaign]:
    query = db.query(Campaign).filter(Campaign.id == campaign_id)
    if company_id:
        query = query.filter(Campaign.company_id == company_id)
    return query.first()


def get_campaigns_by_company(
    db: Session, company_id: UUID, skip: int = 0, limit: int = 100
) -> List[Campaign]:
    return (
        db.query(Campaign)
        .filter(Campaign.company_id == company_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_campaigns(
    db: Session, company_id: Optional[UUID] = None
) -> List[Campaign]:
    query = db.query(Campaign).filter(Campaign.status == CampaignStatus.ACTIVE)
    if company_id:
        query = query.filter(Campaign.company_id == company_id)
    return query.all()


def update_campaign(
    db: Session, db_campaign: Campaign, campaign_in: CampaignUpdate
) -> Campaign:
    update_data = campaign_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_campaign, field, update_data[field])
    db.commit()
    db.refresh(db_campaign)
    return db_campaign
