from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.crud import session as crud_session
from app.schemas.session import SessionCreate, SessionResponse, Session
from app.api.dependencies import get_db

router = APIRouter()


@router.post(
    "/notification-sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate a new notification session",
    response_description="Session creation initiated"
)
async def create_notification_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
):
    """
    Initiate a new notification generation session.
    
    This endpoint creates a new session for generating notifications based on the provided topic.
    The session will be processed asynchronously.
    
    Args:
        session_data: Session creation data including topic, campaign_id, company_id, and admin_id
        db: Database session
        
    Returns:
        SessionResponse with session_id and status
    """
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)
    
    return {
        "session_id": db_session.id,
        "status": db_session.status.value
    }



@router.get(
    "/notification-sessions/{session_id}",
    response_model=Session,
    summary="Get notification session status",
    response_description="Notification session details"
)
async def get_notification_session(
    session_id: UUID,
    company_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status and details of a notification session.
    
    Args:
        session_id: ID of the session to retrieve
        company_id: ID of the company (for authorization)
        db: Database session
        
    Returns:
        The notification session details
    """
    db_session = crud_session.get_notification_session(db, session_id=session_id)
    
    if not db_session or str(db_session.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return db_session

