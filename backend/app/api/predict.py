from fastapi import APIRouter, HTTPException
from app.schemas.schemas import PredictRequest, PredictResponse
from app.services.prediction import prediction_service
from app.core.data import ROADS
import datetime

router = APIRouter()

@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        return prediction_service.predict(req)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Road not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/now/{road_id}", response_model=PredictResponse)
def predict_now(road_id: str, rain_mm: float = 0.0):
    if road_id not in ROADS:
        raise HTTPException(status_code=404, detail=f"Unknown road: {road_id}")
    hour = datetime.datetime.now().hour
    req  = PredictRequest(road_id=road_id, hour=hour, rain_mm=rain_mm)
    return prediction_service.predict(req)
