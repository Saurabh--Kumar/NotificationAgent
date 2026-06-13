import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_db
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus
from app.schemas.session import NotificationSyncResponse, SessionCreate
from app.tasks import run_agent_task


router = APIRouter()


@router.post(
    "/company/{company_id}/notification/sync",
    response_model=NotificationSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Create notification session and return generated notifications",
    response_description="Notification session with generated suggestions",
)
async def create_notification_session_sync(
    company_id: UUID,
    session_data: SessionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a notification generation session, run the agent synchronously, and return
    the generated notifications.

    The response contains the session identifiers, status, and
    generated suggestions. It does not include conversation history.
    """
    # Ensure the company_id in the path matches the one in the request body
    if session_data.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id in path does not match company_id in request body"
        )

    db_session = crud_session.create_notification_session(db=db, session_in=session_data)

    logging.info(
        f"module=app.api.endpoints.notification_sync method=create_notification_session_sync message=Created session {db_session.id}"
    )

    result = run_agent_task(str(db_session.id))

    if result.get("status") != "success":
        logging.error(
            f"module=app.api.endpoints.notification_sync method=create_notification_session_sync message=Task failed: {result.get('message')}"
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
        f"module=app.api.endpoints.notification_sync method=create_notification_session_sync message=Completed sync task for session {db_session.id}"
    )

    return {
        "session_id": db_session.id,
        "status": db_session.status.value,
        "all_suggestions": db_session.all_suggestions or [],
    }
