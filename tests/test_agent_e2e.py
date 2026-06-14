"""End-to-end test for the LangGraph agent with Ollama."""
import json
import time
import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient

from app.agent.tools import fetch_news
from app.agent.agent import tools_node
from app.core.config import settings
from app.tasks import run_agent_task
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus
from app.db.session import SessionLocal
from app.schemas.session import SessionCreate
from app.main import app
from app.api.dependencies import get_db
import app.api.endpoints.notification_sessions as notification_sessions_module
from app.thread_pool import submit_task as real_submit_task


def test_ollama_llm_generates_notifications():
    """Test that the agent can generate notifications using Ollama via run_agent_task."""
    # This test requires Ollama to be running with gemma4:e2b model
    # Uses PostgreSQL database directly (not the in-memory SQLite from conftest)
    db = SessionLocal()
    try:
        # Create a notification session in the DB
        # Using actual campaign from the database (Q2 Product Launch Campaign)
        session_data = SessionCreate(
            topic="sports",
            campaign_id=uuid.UUID("3be6176f-894a-4c0b-87d1-83b9393fe8cb"),
            company_id=uuid.UUID("a639cab1-240b-4d66-b084-751009a88255"),
            admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        )
        test_session = crud_session.create_notification_session(db=db, session_in=session_data)
        db.commit()
        
        # Call the task directly (synchronous execution for e2e test)
        result = run_agent_task(str(test_session.id))
        
        # Verify the result
        assert result is not None, "run_agent_task returned None"
        assert result.get("status") == "success", f"Task failed: {result.get('message')}"
        
        # Refresh the session from DB
        db.refresh(test_session)
        
        # Verify suggestions were generated
        assert test_session.all_suggestions is not None, "all_suggestions is None"
        assert len(test_session.all_suggestions) > 0, "Expected at least one notification suggestion"
        
        # Verify each suggestion has the required fields including news_headline
        for suggestion in test_session.all_suggestions:
            assert "id" in suggestion, "Suggestion missing 'id' field"
            assert "notification_text" in suggestion, "Suggestion missing 'notification_text' field"
            assert "news_headline" in suggestion, "Suggestion missing 'news_headline' field"
            assert "status" in suggestion, "Suggestion missing 'status' field"
        
        # Verify conversation history was updated
        assert test_session.conversation_history is not None
        assert len(test_session.conversation_history) > 0
        
        # Verify status was updated
        assert test_session.status == NotificationSessionStatus.AWAITING_REVIEW
        
        print(f"Generated suggestions: {test_session.all_suggestions}...")
        
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        db.close()


def test_async_notification_session_polling():
    """Test async notification session creation and polling until results are available."""
    original_submit_task = notification_sessions_module.submit_task
    original_override = app.dependency_overrides.get(get_db)

    def real_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = real_get_db
    notification_sessions_module.submit_task = real_submit_task

    try:
        client = TestClient(app)
        request_data = {
            "topic": "sports",
            "campaign_id": "3be6176f-894a-4c0b-87d1-83b9393fe8cb",
            "company_id": "a639cab1-240b-4d66-b084-751009a88255",
            "admin_id": "22222222-2222-2222-2222-222222222222",
        }

        create_response = client.post("/api/v1/notification-sessions", json=request_data)
        if create_response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            pytest.skip("Background worker pool is saturated in test environment; skipping async polling e2e test.")
        assert create_response.status_code == status.HTTP_202_ACCEPTED, create_response.text
        create_data = create_response.json()
        session_id = create_data["session_id"]

        deadline = time.monotonic() + 500
        final_response = None
        while time.monotonic() < deadline:
            final_response = client.get(
                f"/api/v1/company/{request_data['company_id']}/notification-sessions/{session_id}",
            )
            assert final_response.status_code == status.HTTP_200_OK, final_response.text

            final_data = final_response.json()
            if final_data["status"] == NotificationSessionStatus.AWAITING_REVIEW.value:
                assert len(final_data["all_suggestions"]) > 0, "Expected at least one notification suggestion"
                assert "conversation_history" in final_data
                return

            time.sleep(30)

        if final_response is not None:
            pytest.fail(f"Notification session did not reach {NotificationSessionStatus.AWAITING_REVIEW.value} before timeout. Last response: {final_response.text}")
        pytest.fail("Notification session polling did not start")
    finally:
        notification_sessions_module.submit_task = original_submit_task
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        elif get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]


def test_fetch_news_tool():
    """Test that the fetch_news tool can retrieve news (real or dummy for testing)."""
    result = fetch_news.invoke({"news_category": "sports"})
    assert result is not None
    assert len(result) > 0
    # Parse JSON response
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


def test_fetch_news_tool_requires_news_category():
    """Test that fetch_news requires news_category argument."""
    result = fetch_news.invoke({})
    data = json.loads(result)
    
    assert data["error"] is not None
    assert "news_category is required" in data["error"]


def test_tools_node_injects_topic_into_fetch_news(monkeypatch):
    """Test that tools_node passes the selected topic as news_category to fetch_news."""
    invoked_args = {}

    class MockTool:
        def invoke(self, args):
            invoked_args.update(args)
            return json.dumps({"articles": [], "error": None})

    monkeypatch.setattr("app.agent.agent.fetch_news", MockTool())
    monkeypatch.setattr("app.agent.agent.fetch_active_campaigns", MockTool())

    state = {
        "messages": [
            type("Message", (), {"tool_calls": [
                {
                    "name": "fetch_news",
                    "args": {},
                    "id": "call-1"
                }
            ]})
        ],
        "company_id": "a639cab1-240b-4d66-b084-751009a88255",
        "topic": "business"
    }

    result = tools_node(state)

    assert invoked_args == {"news_category": "business"}
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == '{"articles": [], "error": null}'
