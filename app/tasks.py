from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session as DBSession

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus



@celery_app.task(name="app.tasks.run_agent_task")

def run_agent_task(session_id: str) -> dict:
    db: DBSession = SessionLocal()
    
    try:
        session_uuid = UUID(session_id)
        db_session = crud_session.get_notification_session(db, session_id=session_uuid)
        
        if not db_session:
            return {
                "status": "error",
                "message": f"Session {session_id} not found"
            }
        
        # TODO: Implement actual agent logic in future story
        # For now, just update status to AWAITING_REVIEW
        crud_session.update_session_status(
            db=db,
            db_session=db_session,
            status=NotificationSessionStatus.AWAITING_REVIEW
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Agent task placeholder executed"
        }
        
    except Exception as e:
        if db_session:
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.FAILED
            )
        
        return {
            "status": "error",
            "session_id": session_id,
            "message": str(e)
        }
    
    finally:
        db.close()
