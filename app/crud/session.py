from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.notification_session import NotificationSession
from app.models.enums import NotificationSessionStatus
from app.schemas.session import SessionCreate


def create_notification_session(
    db: Session, 
    session_in: SessionCreate
) -> NotificationSession:
    initial_message = {
        "role": "user",
        "content": f"Generate notifications about {session_in.topic}" if session_in.topic 
                  else "Generate notifications"
    }
    
    db_session = NotificationSession(
        id=session_in.id if hasattr(session_in, 'id') else None,
        company_id=session_in.company_id,
        admin_id=session_in.admin_id,
        campaign_id=session_in.campaign_id,
        topic=session_in.topic,
        status=NotificationSessionStatus.PROCESSING,
        conversation_history=[initial_message],
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


def get_notification_session(
    db: Session, 
    session_id: UUID
) -> Optional[NotificationSession]:

    return db.query(NotificationSession).filter(
        NotificationSession.id == session_id
    ).first()


def update_session_status(
    db: Session, 
    db_session: NotificationSession, 
    status: NotificationSessionStatus
) -> NotificationSession:

    db_session.status = status
    db.commit()
    db.refresh(db_session)
    return db_session
