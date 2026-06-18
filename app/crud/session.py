import logging
import uuid
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
        id=session_in.id if hasattr(session_in, 'id') and session_in.id is not None else uuid.uuid4(),
        company_id=session_in.company_id,
        admin_id=session_in.admin_id,
        campaign_id=session_in.campaign_id,
        topic=session_in.topic,
        status=NotificationSessionStatus.PROCESSING,
        conversation_history=[initial_message],
    )
    
    try:
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    except IntegrityError as e:
        db.rollback()
        logging.error(
            f"module=app.crud.session method=create_notification_session message=Database integrity error while creating session for company {session_in.company_id}: {str(e)}"
        )
        raise
    
    if db_session.id is None:
        logging.error(
            f"module=app.crud.session method=create_notification_session message=Session ID is None after commit for company {session_in.company_id}"
        )
        raise RuntimeError("Failed to generate session ID")
    
    logging.info(f"module=app.crud.session method=create_notification_session message=Created session {db_session.id} for company {session_in.company_id}")
    
    return db_session


def get_notification_session(
    db: Session, 
    session_id: UUID,
    company_id: Optional[UUID] = None
) -> Optional[NotificationSession]:

    query = db.query(NotificationSession).filter(
        NotificationSession.id == session_id
    )
    if company_id:
        query = query.filter(NotificationSession.company_id == company_id)
    return query.first()


def update_session_status(
    db: Session, 
    db_session: NotificationSession, 
    status: NotificationSessionStatus
) -> NotificationSession:

    db_session.status = status
    db.commit()
    db.refresh(db_session)
    
    logging.info(f"module=app.crud.session method=update_session_status message=Updated session {db_session.id} status to {status.value}")
    
    return db_session
