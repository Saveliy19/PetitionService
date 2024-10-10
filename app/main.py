from fastapi import FastAPI
from app import statistics_router, petition_router
from starlette.requests import Request
import time

app = FastAPI()


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


