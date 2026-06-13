import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_db
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus
from app.schemas.session import NotificationSessionResult, SessionCreate
from app.tasks import run_agent_task


router = APIRouter()


@router.post(
    "/notification-sessions/sync-result",
    response_model=NotificationSessionResult,
    status_code=status.HTTP_200_OK,
    summary="Create notification session and return generated results",
    response_description="Notification session result with generated suggestions",
)
async def create_notification_session_sync_result(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a notification generation session, run the agent synchronously, and return
    the generated result payload.

    The response intentionally contains only the session identifiers, status, and
    generated suggestions. It does not include conversation history.
    """
    db_session = crud_session.create_notification_session(db=db, session_in=session_data)

    logging.info(
        f"module=app.api.endpoints.notification_session_results method=create_notification_session_sync_result message=Created session {db_session.id}"
    )

    result = run_agent_task(str(db_session.id))

    if result.get("status") != "success":
        logging.error(
            f"module=app.api.endpoints.notification_session_results method=create_notification_session_sync_result message=Task failed: {result.get('message')}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to generate notifications"),
        )

    db.refresh(db_session)

    if db_session.status == NotificationSessionStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate notifications",
        )

    logging.info(
        f"module=app.api.endpoints.notification_session_results method=create_notification_session_sync_result message=Completed sync result task for session {db_session.id}"
    )

    return {
        "session_id": db_session.id,
        "status": db_session.status.value,
        "all_suggestions": db_session.all_suggestions or [],
    }
