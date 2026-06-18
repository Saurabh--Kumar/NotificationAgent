import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.crud import company as crud_company
from app.schemas.company import Company

router = APIRouter()


@router.get(
    "/companies",
    response_model=list[Company],
    summary="Get distinct companies",
    response_description="List of companies derived from campaigns"
)
async def get_companies(db: Session = Depends(get_db)):
    """
    Fetch distinct companies from the campaigns table.
    
    Since there's no separate Company model, companies are derived from
    campaigns.company_id and campaigns.company_name.
    
    Returns:
        List of companies with id and name
    """
    companies = crud_company.get_companies(db)
    logging.info(f"module=app.api.endpoints.companies method=get_companies message=Fetched {len(companies)} companies")
    return companies
