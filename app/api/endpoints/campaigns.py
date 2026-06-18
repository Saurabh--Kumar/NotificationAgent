import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.crud import campaign as crud_campaign
from app.models.enums import CampaignStatus
from app.schemas.campaign import Campaign

router = APIRouter()


@router.get(
    "/companies/{company_id}/campaigns",
    response_model=list[Campaign],
    summary="Get active campaigns for a company",
    response_description="List of active campaigns for the specified company"
)
async def get_campaigns_by_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Fetch active campaigns for a specific company.
    
    Args:
        company_id: ID of the company
        db: Database session
        
    Returns:
        List of active campaigns for the company
    """
    campaigns = crud_campaign.get_active_campaigns(db, company_id)
    logging.info(
        f"module=app.api.endpoints.campaigns method=get_campaigns_by_company "
        f"message=Fetched {len(campaigns)} active campaigns for company_id: {company_id}"
    )
    return campaigns
