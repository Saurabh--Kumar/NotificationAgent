from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/v1",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health", status_code=200)
async def health_check() -> dict:
    """Health check endpoint to verify the service is running."""
    return {"status": "ok"}
