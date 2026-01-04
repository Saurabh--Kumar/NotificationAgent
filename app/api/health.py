from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    tags=["health"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health", status_code=200)
async def health_check() -> dict:
    return {"status": "ok"}
