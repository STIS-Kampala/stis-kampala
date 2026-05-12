from contextlib import asynccontextmanager
from fastapi import FastAPI, Security, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api import predict, roads, models, health, weather, data, collect
import asyncio, os

limiter = Limiter(key_func=get_remote_address)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("API_KEY", "stis-dev-key")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

async def run_collector():
    while True:
        try:
            from app.api.collect import collect as do_collect
            do_collect()
            print("✅ Collector ran successfully")
        except Exception as e:
            print(f"⚠️ Collector error: {e}")
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.core.database import init_db
        init_db()
        print("✅ DB initialized")
    except Exception as e:
        print(f"⚠️ DB init failed: {e}")
    asyncio.create_task(run_collector())
    yield

app = FastAPI(
    title="STIS API",
    description="Smart Traffic Intelligence System - Kampala",
    version="3.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/health",   tags=["health"])
app.include_router(predict.router,  prefix="/predict",  tags=["predict"],  dependencies=[Security(verify_api_key)])
app.include_router(roads.router,    prefix="/roads",     tags=["roads"],    dependencies=[Security(verify_api_key)])
app.include_router(models.router,   prefix="/models",    tags=["models"],   dependencies=[Security(verify_api_key)])
app.include_router(weather.router,  prefix="/weather",   tags=["weather"],  dependencies=[Security(verify_api_key)])
app.include_router(data.router,     prefix="/data",      tags=["data"],     dependencies=[Security(verify_api_key)])
app.include_router(collect.router,  prefix="/collect",   tags=["collect"],  dependencies=[Security(verify_api_key)])

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {"service": "STIS API", "version": "3.0.0", "status": "ok"}
