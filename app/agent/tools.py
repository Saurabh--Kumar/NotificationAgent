import json
import logging
import time
from typing import Optional, List, Tuple
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
            logging.info(f"module=app.agent.tools method=fetch_active_campaigns message=No active campaigns found for company_id: {company_id}")
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
        logging.info(f"module=app.agent.tools method=fetch_active_campaigns message=Fetched {len(campaign_list)} active campaigns for company_id: {company_id}")
        logging.info(f"module=app.agent.tools method=fetch_active_campaigns message=Campaign data: {json.dumps(campaign_list)}")
        return json.dumps({"campaigns": campaign_list, "error": None})
    except Exception as e:
        # Return dummy campaigns for testing when DB is not available
        logging.error(f"module=app.agent.tools method=fetch_active_campaigns message=Error fetching campaigns: {str(e)}")
        return json.dumps({"campaigns": [], "error": f"Failed to fetch campaigns: {str(e)}"})
    finally:
        db.close()


def _validate_news_category(news_category: Optional[str]) -> str:
    """Validate and normalize the news category. Defaults to 'sports' if invalid."""
    if not news_category:
        return "sports"

    valid_categories = ["agriculture", "sports", "business", "technologies", "latest"]
    if news_category not in valid_categories:
        return "sports"

    return news_category


def _fetch_news_with_retry(news_category: str) -> Tuple[Optional[httpx.Response], Optional[Exception]]:
    """Fetch news from the API with exponential backoff retry logic.

    Returns:
        A tuple of (response, last_exception). On success, response is set and exception is None.
        On failure after all retries, response is None and exception contains the last error.
    """
    max_retries = 3
    retry_delay = 5.0  # seconds
    retryable_status_codes = {429, 500, 502, 503, 504}

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            url = f"https://news.knowivate.com/api/{news_category}"

            # Log request details for debugging
            logging.info(
                f"module=app.agent.tools method=fetch_news "
                f"message=Requesting URL: {url} (attempt {attempt}/{max_retries})"
            )

            response = httpx.get(
                url,
                timeout=Timeout(10.0),
                headers={
                    "Accept": "application/json, text/plain, */*",
                }
            )

            # Log response details for debugging
            logging.info(
                f"module=app.agent.tools method=fetch_news "
                f"message=Response body (first 500 chars): {response.text[:500]}"
            )

            # Retry on specific transient HTTP status codes
            if response.status_code in retryable_status_codes:
                if attempt < max_retries:
                    logging.warning(
                        f"module=app.agent.tools method=fetch_news "
                        f"message=Transient HTTP {response.status_code}, retrying in {retry_delay}s "
                        f"(attempt {attempt}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = f"API returned error status {response.status_code} after {max_retries} attempts"
                    logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
                    return None, RuntimeError(error_msg)

            response.raise_for_status()
            return response, None

        except httpx.RequestError as e:
            last_exception = e
            if attempt < max_retries:
                logging.warning(
                    f"module=app.agent.tools method=fetch_news "
                    f"message=Network error: {str(e)}, retrying in {retry_delay}s "
                    f"(attempt {attempt}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                error_msg = f"Network error fetching news after {max_retries} attempts: {str(e)}"
                logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
                return None, RuntimeError(error_msg)
        except httpx.HTTPStatusError as e:
            last_exception = e
            if e.response.status_code in retryable_status_codes and attempt < max_retries:
                logging.warning(
                    f"module=app.agent.tools method=fetch_news "
                    f"message=HTTP {e.response.status_code}, retrying in {retry_delay}s "
                    f"(attempt {attempt}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                error_msg = f"API returned error status {e.response.status_code}"
                logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
                return None, RuntimeError(error_msg)
        except (ValueError, json.JSONDecodeError) as e:
            # Don't retry on parse errors - they're likely not transient
            error_msg = f"Failed to parse news response: {str(e)}"
            logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
            return None, RuntimeError(error_msg)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logging.warning(
                    f"module=app.agent.tools method=fetch_news "
                    f"message=Unexpected error: {str(e)}, retrying in {retry_delay}s "
                    f"(attempt {attempt}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                error_msg = f"Unexpected error after {max_retries} attempts: {str(e)}"
                logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
                return None, RuntimeError(error_msg)

    # Should not reach here, but handle defensively
    error_msg = f"Unexpected error after {max_retries} attempts: {str(last_exception)}"
    logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
    return None, RuntimeError(error_msg)


def _parse_news_response(data: dict, news_category: str) -> List[dict]:
    """Parse the API response data and return a simplified list of news articles.

    Raises:
        RuntimeError: If the API indicates failure or no articles are found.
    """
    if not data.get("success"):
        error_msg = f"API error: {data.get('message', 'Unknown error')}"
        logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
        raise RuntimeError(error_msg)

    news_items = data.get("news", [])
    if not news_items:
        logging.info(f"module=app.agent.tools method=fetch_news message=No news articles found for category: {news_category}")
        raise RuntimeError("No news articles found")

    # Return simplified article data
    news_list = [
        {
            "title": item.get("title", ""),
            "description": item.get("description", ""),
        }
        for item in news_items[:5]  # Limit to 5 articles
    ]
    logging.info(f"module=app.agent.tools method=fetch_news message=Fetched {len(news_list)} articles for category: {news_category}")
    logging.info(f"module=app.agent.tools method=fetch_news message=News data: {json.dumps(news_list)}")
    return news_list


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
    news_category = _validate_news_category(news_category)
    logging.info(f"module=app.agent.tools method=fetch_news message=Fetching news for category: {news_category}")

    response, error = _fetch_news_with_retry(news_category)
    if error:
        return json.dumps({"articles": [], "error": str(error)})

    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError) as e:
        error_msg = f"Failed to parse news response: {str(e)}"
        logging.error(f"module=app.agent.tools method=fetch_news message={error_msg}")
        return json.dumps({"articles": [], "error": error_msg})

    try:
        news_list = _parse_news_response(data, news_category)
    except RuntimeError as e:
        return json.dumps({"articles": [], "error": str(e)})

    return json.dumps({"articles": news_list, "error": None})
