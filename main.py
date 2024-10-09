from fastapi import FastAPI
#from fastapi.middleware.cors import CORSMiddleware
from app import statistics_router, petition_router
from app import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

app = FastAPI()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        inf = f"Запрос: {request.method} {request.url} Headers: {request.headers} Body: {await request.body()}"
        response = await call_next(request)
        
        if response.status_code >= 400:
            execution_time = time.time() - start_time
            logger.error(f"Ошибка: {response.status_code} {request.method} {request.url} Время выполнения: {execution_time:.2f} сек, {inf}")
        
        return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.add_middleware(LoggingMiddleware)

app.include_router(petition_router, prefix="/petitions")
app.include_router(statistics_router, prefix="/statistics")
