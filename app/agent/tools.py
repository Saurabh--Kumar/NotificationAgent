from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from langchain.tools import tool

from app.crud.campaign import get_active_campaigns
from app.schemas.campaign import Campaign


@tool
def fetch_active_campaigns(company_id: Optional[str] = None) -> str:
    """Fetch all active campaigns, optionally filtered by company ID. Returns a list of active campaigns with their details."""
    # Note: db session will be injected when the tool is invoked via the agent context
    # This tool expects a db session to be available in the agent's state
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        company_uuid = UUID(company_id) if company_id else None
        campaigns = get_active_campaigns(db, company_uuid)
        if not campaigns:
            return "No active campaigns found."
        campaign_list = [
            {
                "id": str(c.id),
                "company_id": str(c.company_id),
                "company_name": c.company_name,
                "name": c.name,
                "theme": c.theme,
                "category": c.category,
                "brand_voice": c.brand_voice,
                "target_audience": c.target_audience,
                "industry": c.industry,
            }
            for c in campaigns
        ]
        return str(campaign_list)
    finally:
        db.close()


@tool
def fetch_dummy_news(topic: Optional[str] = None) -> str:
    """Fetch dummy news articles related to the given topic. Returns a list of dummy news articles."""
    dummy_news = [
        {"title": "New Product Launch", "content": "Company launches new product line targeting young adults.", "topic": "product"},
        {"title": "Industry Growth Report", "content": "2024 industry report shows 15% growth in tech sector.", "topic": "industry"},
        {"title": "Customer Engagement Strategies", "content": "Top 5 strategies to boost customer engagement via notifications.", "topic": "marketing"},
        {"title": "AI in Marketing", "content": "How AI is transforming personalized marketing campaigns.", "topic": "technology"},
    ]
    if topic:
        filtered = [n for n in dummy_news if topic.lower() in n["topic"].lower()]
        return str(filtered) if filtered else "No dummy news found for this topic."
    return str(dummy_news)
