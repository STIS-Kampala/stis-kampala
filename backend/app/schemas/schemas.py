from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

CongestionLabel = Literal["low", "medium", "high"]
ModelName = Literal["gradient_boosting", "random_forest", "ridge"]

class PredictRequest(BaseModel):
    road_id:  str
    hour:     int = Field(..., ge=0, le=23)
    rain_mm:  float = Field(0.0, ge=0.0)
    model:    ModelName = "gradient_boosting"

class ConfidenceInterval(BaseModel):
    lower: float
    upper: float

class SHAPInfo(BaseModel):
    top_feature: str
    value:       float

class RiskInfo(BaseModel):
    accident: int
    flood:    int

class CostInfo(BaseModel):
    extra_fuel_l_per_100km: float
    extra_co2_g:            int

class PredictResponse(BaseModel):
    road_id:       str
    road_name:     str
    label:         CongestionLabel
    confidence:    float
    delay_ratio:   float
    ci_95:         ConfidenceInterval
    travel_min:    float
    base_min:      int
    shap:          SHAPInfo
    risk:          RiskInfo
    cost:          CostInfo
    model_used:    ModelName
    model_version: str
    latency_ms:    int

class RoadMeta(BaseModel):
    id:       str
    name:     str
    type:     str
    base_min: int
    km:       float
    has_boda: bool
    label:    CongestionLabel

class ModelMetrics(BaseModel):
    mae:      float
    rmse:     float
    r2:       float
    accuracy: float
    f1:       float
    cv_mae:   float
    cv_std:   float

class ModelInfo(BaseModel):
    name:     ModelName
    label:    str
    version:  str
    metrics:  ModelMetrics
    is_best:  bool

class HealthResponse(BaseModel):
    status:        Literal["ok", "degraded"]
    version:       str
    models_loaded: bool
