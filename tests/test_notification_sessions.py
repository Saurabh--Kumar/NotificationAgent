import json
import uuid
from fastapi import status
from sqlalchemy.orm import Session

from app.models.notification_session import NotificationSession, NotificationSessionStatus
from app.schemas.session import SessionCreate
from app.crud import session as crud_session


def test_create_notification_session(client, db: Session, test_company_id, test_admin_id, test_campaign_id):
    request_data = {
        "topic": "Test Topic",
        "campaign_id": test_campaign_id,
        "company_id": test_company_id,
        "admin_id": test_admin_id
    }

    response = client.post(
        "/api/v1/notification-sessions",
        json=request_data
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "session_id" in data
    assert data["status"] == NotificationSessionStatus.PROCESSING.value

    session_id = uuid.UUID(data["session_id"])
    db_session = db.query(NotificationSession).filter(NotificationSession.id == session_id).first()

    assert db_session is not None
    assert str(db_session.company_id) == test_company_id
    assert str(db_session.admin_id) == test_admin_id
    assert str(db_session.campaign_id) == test_campaign_id
    assert db_session.topic == "Test Topic"
    assert db_session.status == NotificationSessionStatus.PROCESSING
    assert len(db_session.conversation_history) == 1
    assert db_session.conversation_history[0]["role"] == "user"
    assert "Test Topic" in db_session.conversation_history[0]["content"]



def test_create_session_without_topic(client, test_company_id, test_admin_id, test_campaign_id):
    request_data = {
        "campaign_id": test_campaign_id,
        "company_id": test_company_id,
        "admin_id": test_admin_id
    }
    
    response = client.post(
        "/api/v1/notification-sessions",
        json=request_data
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "session_id" in data


def test_create_session_missing_campaign_id(client, test_company_id, test_admin_id):
    request_data = {
        "topic": "Test Topic",
        "company_id": test_company_id,
        "admin_id": test_admin_id
    }
    
    response = client.post(
        "/api/v1/notification-sessions",
        json=request_data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_notification_session(client, db: Session, test_company_id, test_campaign_id):
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id)
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db.commit()

    response = client.get(
        f"/api/v1/company/{test_company_id}/notification-sessions/{db_session.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["id"] == str(db_session.id)
    assert data["company_id"] == test_company_id
    assert data["campaign_id"] == test_campaign_id
    assert data["status"] == NotificationSessionStatus.PROCESSING.value
    assert data["topic"] == "Test Topic"
    assert "conversation_history" in data

    # Verify response is proper JSON serializable format
    assert json.dumps(data, ensure_ascii=False)


def test_get_nonexistent_session(client):
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/company/11111111-1111-1111-1111-111111111111/notification-sessions/{non_existent_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.text


def test_get_session_wrong_company_id(client, db: Session, test_company_id, test_campaign_id):
    """Test that requesting a session with wrong company_id returns 404 (multi-tenancy enforcement)."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id)
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db.commit()

    # Try to access with a different company_id
    wrong_company_id = "99999999-9999-9999-9999-999999999999"
    response = client.get(
        f"/api/v1/company/{wrong_company_id}/notification-sessions/{db_session.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.text


def test_add_feedback(client, db: Session, test_company_id, test_campaign_id):
    """Test appending feedback to a notification session."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id)
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db.commit()

    feedback_data = {"feedback": "Make it more exciting and urgent"}
    response = client.post(
        f"/api/v1/company/{test_company_id}/notification-sessions/{db_session.id}/feedback",
        json=feedback_data,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["conversation_history"]) == 2
    assert data["conversation_history"][-1]["role"] == "user"
    assert "Make it more exciting and urgent" in data["conversation_history"][-1]["content"]
    assert json.dumps(data, ensure_ascii=False)


def test_add_feedback_nonexistent_session(client):
    """Test that adding feedback to a non-existent session returns 404."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    feedback_data = {"feedback": "Some feedback"}
    response = client.post(
        f"/api/v1/company/11111111-1111-1111-1111-111111111111/notification-sessions/{non_existent_id}/feedback",
        json=feedback_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_publish_notifications(client, db: Session, test_company_id, test_campaign_id):
    """Test publishing selected notifications for a session."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id)
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    # Manually set suggestions for testing
    db_session.all_suggestions = [
        {"id": "sugg-1", "notification_text": "Notification 1", "status": "pending"},
        {"id": "sugg-2", "notification_text": "Notification 2", "status": "pending"},
        {"id": "sugg-3", "notification_text": "Notification 3", "status": "pending"},
    ]
    db_session.status = NotificationSessionStatus.AWAITING_REVIEW
    db.commit()

    publish_data = {"selected_suggestion_ids": ["sugg-1", "sugg-3"]}
    response = client.post(
        f"/api/v1/company/{test_company_id}/notification-sessions/{db_session.id}/publish",
        json=publish_data,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == NotificationSessionStatus.COMPLETED.value
    assert len(data["selected_suggestions"]) == 2
    assert data["selected_suggestions"][0]["id"] == "sugg-1"
    assert data["selected_suggestions"][1]["id"] == "sugg-3"
    assert json.dumps(data, ensure_ascii=False)


def test_publish_notifications_nonexistent_session(client):
    """Test that publishing for a non-existent session returns 404."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    publish_data = {"selected_suggestion_ids": ["sugg-1"]}
    response = client.post(
        f"/api/v1/company/11111111-1111-1111-1111-111111111111/notification-sessions/{non_existent_id}/publish",
        json=publish_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_publish_notifications_invalid_ids(client, db: Session, test_company_id, test_campaign_id):
    """Test that publishing with invalid suggestion IDs returns 400."""
    session_data = SessionCreate(
        topic="Test Topic",
        company_id=uuid.UUID(test_company_id),
        admin_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        campaign_id=uuid.UUID(test_campaign_id)
    )
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    db_session.all_suggestions = [
        {"id": "sugg-1", "notification_text": "Notification 1", "status": "pending"},
    ]
    db_session.status = NotificationSessionStatus.AWAITING_REVIEW
    db.commit()

    publish_data = {"selected_suggestion_ids": ["non-existent-id"]}
    response = client.post(
        f"/api/v1/company/{test_company_id}/notification-sessions/{db_session.id}/publish",
        json=publish_data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No valid suggestions selected" in response.text