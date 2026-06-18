import logging
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.campaign import Campaign


def get_companies(db: Session) -> List[dict]:
    """
    Fetch distinct companies from campaigns table.
    Since there's no separate Company model, derive companies from campaigns.
    """
    companies = (
        db.query(Campaign.company_id, Campaign.company_name)
        .group_by(Campaign.company_id, Campaign.company_name)
        .order_by(Campaign.company_name)
        .all()
    )
    
    company_list = [
        {"id": company_id, "name": company_name}
        for company_id, company_name in companies
    ]
    
    logging.info(f"module=app.crud.company method=get_companies message=Fetched {len(company_list)} companies")
    return company_list
