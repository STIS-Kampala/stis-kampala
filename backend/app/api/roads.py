from fastapi import APIRouter
from app.core.data import ROADS
from app.schemas.schemas import RoadMeta

router = APIRouter()

@router.get("", response_model=list[RoadMeta])
def list_roads():
    return [
        RoadMeta(
            id=r.id,
            name=r.name,
            type=r.type,
            base_min=r.base_min,
            km=r.km,
            has_boda=r.has_boda,
            label=r.label,
        )
        for r in ROADS.values()
    ]
