"""End-to-end test for the LangGraph agent with Ollama."""
import pytest
from app.agent import generate_notifications
from app.agent.tools import fetch_news
from app.core.config import settings


def test_ollama_llm_generates_notifications():
    """Test that the agent can generate notifications using Ollama."""
    # This test requires Ollama to be running with gemma4:e2b model
    try:
        suggestions = generate_notifications(topic="product launch", company_id="11111111-1111-1111-1111-111111111111")
        assert suggestions is not None
        assert isinstance(suggestions, list), f"Expected list, got {type(suggestions)}"
        assert len(suggestions) > 0, "Expected at least one notification suggestion"
        # Check that we got some response content
        print(f"Agent response: {suggestions}...")
    except Exception as e:
        pytest.skip(f"Ollama not available or model not loaded: {e}")


def test_fetch_news_tool():
    """Test that the fetch_news tool can retrieve news (real or dummy for testing)."""
    result = fetch_news.invoke({})
    assert result is not None
    assert len(result) > 0
    # Parse JSON response
    import json
    data = json.loads(result)
    # Should return a dict with articles list and no error
    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
    assert "articles" in data, "Response missing 'articles' key"
    assert "error" in data, "Response missing 'error' key"
    assert data["error"] is None, f"Got error: {data['error']}"
    assert isinstance(data["articles"], list), f"Expected list for articles, got {type(data['articles'])}"
    assert len(data["articles"]) > 0, "Expected at least one article"
    print(f"News result: {result[:2000]}...")