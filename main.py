from fastapi import FastAPI
#from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI()

# Разрешить запросы с любых источников (*)
'''app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

app.include_router(router)
