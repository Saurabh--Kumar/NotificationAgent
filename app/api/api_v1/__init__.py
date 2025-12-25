from fastapi import APIRouter

from app.api.endpoints import notification_sessions

api_router = APIRouter()

api_router.include_router(
    notification_sessions.router,
    prefix="/api/v1",
    tags=["notification-sessions"]
)
