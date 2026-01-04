from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.endpoints.notification_sessions import router as notification_sessions_router

app = FastAPI(
    title="Notification Agent API",
    description="API for generating and managing notification suggestions",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(notification_sessions_router, prefix="/api/v1", tags=["Notification Sessions"])



