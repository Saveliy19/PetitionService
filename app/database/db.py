import asyncpg
from app.logger import logger
from app.config import settings


class DataBase:
    def __init__(self, host, port, user, database, password):
        self.host = host
        self.port = port
        self.user = user
        self.database = database
        self.password = password
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(host=self.host,
                                                  port=self.port,
                                                  user=self.user,
                                                  database=self.database,
                                                  password=self.password,
                                                  min_size=1,
                                                  max_size=10)
            logger.info("Успешно подключено к базе данных")
        except asyncpg.PostgresError as e:
            logger.error("Ошибка подключения к БД", e)
        except Exception as e:
            logger.exception("Непредвиденная ошибка при подключении к БД", exc_info=e)

    async def select_query(self, query, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                async with connection.transaction():
                    result = await connection.fetch(query, *args)
                    return result
            except asyncpg.PostgresError as e:
                logger.error(f'Ошибка при исполнении запроса: {query} с параметрами: {args}. Ошибка: {e}')
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при исполнении запроса {query} с параметрами: {args}", exc_info=e)

    async def select_one(self, query, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                async with connection.transaction():
                    result = await connection.fetchrow(query, *args)
                    return result
            except asyncpg.PostgresError as e:
                logger.error(f'Ошибка при исполнении запроса: {query} с параметрами: {args}. Ошибка: {e}')
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при исполнении запроса {query} с параметрами: {args}", exc_info=e)

    async def exec_query(self, query, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                async with connection.transaction():
                    await connection.execute(query, *args)
            except asyncpg.PostgresError as e:
                logger.error(f'Ошибка при исполнении запроса: {query} с параметрами: {args}. Ошибка: {e}')
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при выполнении запроса {query} с параметрами: {args}", exc_info=e)

    async def exec_many_query(self, query_map):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                async with connection.transaction():
                    for query, args in query_map.items():
                        await connection.execute(query, *args)
            except asyncpg.PostgresError as e:
                logger.error(f'Ошибка при исполнении запроса: {query} с параметрами: {args}. Ошибка: {e}')
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при выполнении запроса {query} с параметрами: {args}", exc_info=e)
        return True

    async def insert_returning(self, query, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                async with connection.transaction():
                    result = await connection.fetchval(query, *args)
                    return result
            except asyncpg.PostgresError as e:
                logger.error(f'Ошибка при исполнении запроса: {query} с параметрами: {args}. Ошибка: {e}')
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при выполнении запроса {query} с параметрами: {args}", exc_info=e)

    async def close_connection(self):
        if self.pool:
            await self.pool.close()


db = DataBase(settings.host, settings.port, settings.user, settings.database, settings.password)
