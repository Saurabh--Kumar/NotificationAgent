import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure application INFO logs are visible in the console
logging.basicConfig(level=logging.INFO)

from app.api.health import router as health_router
from app.api.endpoints.notification_sessions import router as notification_sessions_router
from app.api.endpoints.notification_sync import router as notification_sync_router
from app.thread_pool import shutdown as shutdown_thread_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    shutdown_thread_pool(wait=False)


app = FastAPI(
    title="Notification Agent API",
    description="API for generating and managing notification suggestions",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(notification_sync_router, prefix="/api/v1", tags=["Notification Sync"])



