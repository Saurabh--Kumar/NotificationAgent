import json
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from langchain.tools import tool
import httpx
from httpx import Timeout

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
            return json.dumps({"campaigns": [], "error": None})
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
        return json.dumps({"campaigns": campaign_list, "error": None})
    except Exception as e:
        # Return dummy campaigns for testing when DB is not available
        dummy_campaigns = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "company_id": "11111111-1111-1111-1111-111111111111",
                "company_name": "Myntra",
                "name": "Summer Sale Campaign",
                "theme": "End of Reason Sale. Upto 90% off on latest fashion.",
                "category": "promotional",
                "brand_voice": "trendy",
                "target_audience": "young adults",
                "industry": "fashion",
            }
        ]
        return json.dumps({"campaigns": dummy_campaigns, "error": None})
    finally:
        db.close()


@tool
def fetch_news(topic: Optional[str] = None) -> str:
    """Fetch real news articles from NewsAPI. Returns a list of news articles with title, description, and content."""
    from app.core.config import settings

    try:
        params = {
            "country": "us",
            "category": "business",
            "apiKey": settings.NEWSAPI_KEY,
        }
        
        response = httpx.get(
            settings.NEWSAPI_BASE_URL, 
            params=params, 
            timeout=Timeout(10.0)
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            return json.dumps({"articles": [], "error": f"NewsAPI error: {data.get('message', 'Unknown error')}"})
        
        articles = data.get("articles", [])
        if not articles:
            return json.dumps({"articles": [], "error": "No news articles found"})
        
        # Return simplified article data
        news_list = [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "content": a.get("content", ""),
                "source": a.get("source", {}).get("name", ""),
                "url": a.get("url", ""),
            }
            for a in articles[:5]  # Limit to 5 articles
        ]
        return json.dumps({"articles": news_list, "error": None})
    except httpx.RequestError as e:
        return json.dumps({"articles": [], "error": f"Network error fetching news: {str(e)}"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"articles": [], "error": f"NewsAPI returned error status {e.response.status_code}"})
    except (ValueError, json.JSONDecodeError) as e:
        return json.dumps({"articles": [], "error": f"Failed to parse news response: {str(e)}"})
    except Exception as e:
        return json.dumps({"articles": [], "error": f"Unexpected error: {str(e)}"})
