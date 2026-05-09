from fastapi import APIRouter
from app.schemas.schemas import HealthResponse

router = APIRouter()

@router.get("", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        version="3.0.0",
        models_loaded=True,
    )
