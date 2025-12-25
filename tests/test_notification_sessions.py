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
        f"/api/v1/notification-sessions/{db_session.id}",
        params={"company_id": test_company_id}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["id"] == str(db_session.id)
    assert data["company_id"] == test_company_id
    assert data["campaign_id"] == test_campaign_id
    assert data["status"] == NotificationSessionStatus.PROCESSING.value
    assert data["topic"] == "Test Topic"
    assert "conversation_history" in data


def test_get_nonexistent_session(client):
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/notification-sessions/{non_existent_id}",
        params={"company_id": "11111111-1111-1111-1111-111111111111"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.text