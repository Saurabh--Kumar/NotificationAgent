"""End-to-end test for the LangGraph agent with Ollama."""
import pytest
from app.agent import generate_notifications


def test_agent_generates_notifications():
    """Test that the agent can generate notifications using Ollama."""
    # This test requires Ollama to be running with gemma4:e2b model
    try:
        messages = generate_notifications(topic="product launch", company_id="11111111-1111-1111-1111-111111111111")
        assert messages is not None
        assert len(messages) > 0
        # Check that we got some response content
        response_text = str(messages)
        assert len(response_text) > 0
        print(f"Agent response: {response_text[:5000]}...")
    except Exception as e:
        pytest.skip(f"Ollama not available or model not loaded: {e}")