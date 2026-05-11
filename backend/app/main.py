from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import predict, roads, models, health, weather, data

app = FastAPI(
    title="STIS API",
    description="Smart Traffic Intelligence System - Kampala",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,  prefix="/health",  tags=["health"])
app.include_router(predict.router, prefix="/predict", tags=["predict"])
app.include_router(roads.router,   prefix="/roads",   tags=["roads"])
app.include_router(models.router,  prefix="/models",  tags=["models"])
app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(data.router,    prefix="/data",    tags=["data"])

@app.get("/")
def root():
    return {"service": "STIS API", "version": "3.0.0", "status": "ok"}
