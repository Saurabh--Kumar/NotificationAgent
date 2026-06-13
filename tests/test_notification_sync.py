import uuid
from unittest.mock import patch
from fastapi import status
from sqlalchemy.orm import Session

from app.models.notification_session import NotificationSessionStatus
from app.schemas.session import SessionCreate
from app.crud import session as crud_session
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.api.endpoints.notification_sync.run_agent_task")
def test_create_notification_session_sync_success(mock_run_agent_task, client, db: Session, test_company_id, test_campaign_id):
    """Test synchronous session creation returns suggestions."""
    mock_run_agent_task.return_value = {"status": "success"}

    request_data = {
        "topic": "Test Topic",
        "campaign_id": test_campaign_id,
        "company_id": test_company_id,
        "admin_id": "22222222-2222-2222-2222-222222222222",
    }

    response = client.post(
        f"/api/v1/company/{test_company_id}/notification/sync",
        json=request_data,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "session_id" in data
    assert "status" in data
    assert "all_suggestions" in data


def test_create_notification_session_sync_company_id_mismatch(client, test_company_id, test_campaign_id):
    """Test that mismatched company_id in path vs body returns 400."""
    wrong_company_id = str(uuid.uuid4())
    request_data = {
        "topic": "Test Topic",
        "campaign_id": test_campaign_id,
        "company_id": test_company_id,
        "admin_id": "22222222-2222-2222-2222-222222222222",
    }

    response = client.post(
        f"/api/v1/company/{wrong_company_id}/notification/sync",
        json=request_data,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "company_id in path does not match" in response.json()["detail"]


def test_create_notification_session_sync_missing_campaign_id(client, test_company_id):
    """Test that missing campaign_id returns 422."""
    request_data = {
        "topic": "Test Topic",
        "company_id": test_company_id,
        "admin_id": "22222222-2222-2222-2222-222222222222",
    }

    response = client.post(
        f"/api/v1/company/{test_company_id}/notification/sync",
        json=request_data,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_notification_session_wrong_company_id_in_path(client, db: Session, test_company_id, test_campaign_id):
    """Test that accessing a session with wrong company_id in path returns 404."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id),
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db.commit()

    wrong_company_id = str(uuid.uuid4())
    response = client.get(
        f"/api/v1/company/{wrong_company_id}/notification-sessions/{db_session.id}",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.text


def test_add_feedback_wrong_company_id_in_path(client, db: Session, test_company_id, test_campaign_id):
    """Test that adding feedback with wrong company_id in path returns 404."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id),
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db.commit()

    wrong_company_id = str(uuid.uuid4())
    feedback_data = {"feedback": "Make it more exciting"}
    response = client.post(
        f"/api/v1/company/{wrong_company_id}/notification-sessions/{db_session.id}/feedback",
        json=feedback_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_publish_notifications_wrong_company_id_in_path(client, db: Session, test_company_id, test_campaign_id):
    """Test that publishing with wrong company_id in path returns 404."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id),
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db_session.all_suggestions = [
        {"id": "sugg-1", "notification_text": "Notification 1", "status": "pending"},
    ]
    db_session.status = NotificationSessionStatus.AWAITING_REVIEW
    db.commit()

    wrong_company_id = str(uuid.uuid4())
    publish_data = {"selected_suggestion_ids": ["sugg-1"]}
    response = client.post(
        f"/api/v1/company/{wrong_company_id}/notification-sessions/{db_session.id}/publish",
        json=publish_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_notification_session_invalid_uuid_format(client):
    """Test that invalid UUID format in path returns 422 (FastAPI validation)."""
    response = client.get(
        "/api/v1/company/not-a-uuid/notification-sessions/not-a-uuid",
    )

    # FastAPI returns 422 for invalid UUID path parameters
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
