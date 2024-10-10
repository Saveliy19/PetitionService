import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("PORT")
    user: str = os.getenv("USER")
    database: str = os.getenv("DB_NAME")
    password: str = os.getenv("PASSWORD")
    photos_directory: str = os.getenv("PHOTOS_DIRECTORY")


settings = Settings()