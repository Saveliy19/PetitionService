from fastapi import FastAPI
from app import statistics_router, petition_router, like_router
from starlette.requests import Request
import time

from .config import settings

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = await aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response



app.include_router(petition_router,
                   prefix="/petitions",
                   tags=["Петиции"])

app.include_router(statistics_router,
                   prefix="/statistics",
                   tags=["Статистика"])

app.include_router(like_router,
                   prefix="/like",
                   tags=["Лайки"])


