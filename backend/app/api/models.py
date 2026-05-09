from fastapi import APIRouter
from app.schemas.schemas import ModelInfo, ModelMetrics

router = APIRouter()

MODELS = [
    ModelInfo(
        name="gradient_boosting",
        label="Gradient Boosting",
        version="v2.0",
        is_best=True,
        metrics=ModelMetrics(
            mae=0.0723, rmse=0.0982, r2=0.9754,
            accuracy=0.9375, f1=0.8991,
            cv_mae=0.0596, cv_std=0.0029,
        ),
    ),
    ModelInfo(
        name="random_forest",
        label="Random Forest",
        version="v2.0",
        is_best=False,
        metrics=ModelMetrics(
            mae=0.0803, rmse=0.1136, r2=0.9671,
            accuracy=0.9090, f1=0.8499,
            cv_mae=0.0599, cv_std=0.0055,
        ),
    ),
    ModelInfo(
        name="ridge",
        label="Ridge Regression",
        version="v2.0",
        is_best=False,
        metrics=ModelMetrics(
            mae=0.1438, rmse=0.1846, r2=0.9130,
            accuracy=0.9213, f1=0.8704,
            cv_mae=0.1396, cv_std=0.0038,
        ),
    ),
]

@router.get("", response_model=list[ModelInfo])
def list_models():
    return MODELS
