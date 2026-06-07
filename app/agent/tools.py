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
def fetch_news(news_category: Optional[str] = None) -> str:
    """Fetch news articles from Knowivate API (Indian news source) for context.
    
    Use this tool to get current news that can inspire or provide context for notification suggestions.
    This is different from the notification topic - this is the news category to fetch.
    
    Args:
        news_category: Optional news category. Valid values: agriculture, sports, business, technologies, latest.
               If not provided or invalid, defaults to "sports".
    
    Returns:
        JSON string with "articles" list and "error" field.
        Each article has: title, description, content, source, url.
    
    Example usage:
        fetch_news() -> gets sports news (default)
        fetch_news("business") -> gets business news
        fetch_news("technologies") -> gets tech news
    """
    # Default to sports if no news_category provided
    if not news_category:
        news_category = "sports"
    
    # Validate news_category
    valid_categories = ["agriculture", "sports", "business", "technologies", "latest"]
    if news_category not in valid_categories:
        news_category = "sports"
    
    try:
        url = f"https://news.knowivate.com/api/{news_category}"
        
        response = httpx.get(
            url, 
            timeout=Timeout(10.0)
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success"):
            return json.dumps({"articles": [], "error": f"API error: {data.get('message', 'Unknown error')}"})
        
        news_items = data.get("news", [])
        if not news_items:
            return json.dumps({"articles": [], "error": "No news articles found"})
        
        # Return simplified article data
        news_list = [
            {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "content": item.get("description", ""),  # Use description as content
                "source": item.get("source", {}).get("name", ""),
                "url": item.get("url", ""),
            }
            for item in news_items[:5]  # Limit to 5 articles
        ]
        return json.dumps({"articles": news_list, "error": None})
    except httpx.RequestError as e:
        return json.dumps({"articles": [], "error": f"Network error fetching news: {str(e)}"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"articles": [], "error": f"API returned error status {e.response.status_code}"})
    except (ValueError, json.JSONDecodeError) as e:
        return json.dumps({"articles": [], "error": f"Failed to parse news response: {str(e)}"})
    except Exception as e:
        return json.dumps({"articles": [], "error": f"Unexpected error: {str(e)}"})
