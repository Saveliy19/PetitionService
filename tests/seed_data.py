import asyncio
import asyncpg

from app.config import settings

pool = asyncpg.create_pool(host=settings.host, 
                            port=settings.port, 
                            user=settings.user, 
                            database=settings.database, 
                            password=settings.password, 
                            min_size=1,
                            max_size=10)

async def seed_data():
    pass
    pool.close()