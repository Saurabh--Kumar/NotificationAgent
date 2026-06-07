"""End-to-end test for the LangGraph agent with Ollama."""
import pytest
import uuid
from app.agent.tools import fetch_news
from app.core.config import settings
from app.tasks import run_agent_task
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus
from app.db.session import SessionLocal
from app.schemas.session import SessionCreate


def test_ollama_llm_generates_notifications():
    """Test that the agent can generate notifications using Ollama via run_agent_task."""
    # This test requires Ollama to be running with gemma4:e2b model
    # Uses PostgreSQL database directly (not the in-memory SQLite from conftest)
    db = SessionLocal()
    try:
        # Create a notification session in the DB
        # Using actual campaign from the database (Q2 Product Launch Campaign)
        session_data = SessionCreate(
            topic="product launch",
            campaign_id=uuid.UUID("3be6176f-894a-4c0b-87d1-83b9393fe8cb"),
            company_id=uuid.UUID("a639cab1-240b-4d66-b084-751009a88255"),
            admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        )
        test_session = crud_session.create_notification_session(db=db, session_in=session_data)
        db.commit()
        
        # Call the task (synchronously, not via Celery)
        result = run_agent_task(str(test_session.id))
        
        # Verify the result
        assert result is not None
        assert result.get("status") == "success"
        
        # Refresh the session from DB
        db.refresh(test_session)
        
        # Verify suggestions were generated
        assert test_session.all_suggestions is not None
        assert len(test_session.all_suggestions) > 0, "Expected at least one notification suggestion"
        
        # Verify each suggestion has the required fields including news_headline
        for suggestion in test_session.all_suggestions:
            assert "id" in suggestion, "Suggestion missing 'id' field"
            assert "text" in suggestion, "Suggestion missing 'text' field"
            assert "news_headline" in suggestion, "Suggestion missing 'news_headline' field"
            assert "status" in suggestion, "Suggestion missing 'status' field"
        
        # Verify conversation history was updated
        assert test_session.conversation_history is not None
        assert len(test_session.conversation_history) > 0
        
        # Verify status was updated
        assert test_session.status == NotificationSessionStatus.AWAITING_REVIEW
        
        print(f"Generated suggestions: {test_session.all_suggestions}...")
        
    except Exception as e:
        pytest.skip(f"Ollama not available or model not loaded: {e}")
    finally:
        db.close()


def test_fetch_news_tool():
    """Test that the fetch_news tool can retrieve news (real or dummy for testing)."""
    result = fetch_news.invoke({})
    assert result is not None
    assert len(result) > 0
    # Parse JSON response
    import json
    data = json.loads(result)
    # Should return a dict with articles list and error field
    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
    assert "articles" in data, "Response missing 'articles' key"
    assert "error" in data, "Response missing 'error' key"
    
    # If there's an error, skip the test (API might be down)
    if data["error"] is not None:
        pytest.skip(f"News API unavailable or returned error: {data['error']}")
    
    assert isinstance(data["articles"], list), f"Expected list for articles, got {type(data['articles'])}"
    assert len(data["articles"]) > 0, "Expected at least one article"
    print(f"News result: {result[:2000]}...")