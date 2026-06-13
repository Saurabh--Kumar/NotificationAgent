from fastapi import APIRouter

from app.api.endpoints import notification_session_results, notification_sessions

api_router = APIRouter()

api_router.include_router(
    notification_sessions.router,
    prefix="/api/v1",
    tags=["notification-sessions"]
)
api_router.include_router(
    notification_session_results.router,
    prefix="/api/v1",
    tags=["notification-session-results"]
)
