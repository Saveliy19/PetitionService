import asyncpg
from asyncpg import Record
from typing import List



class DataBase:
    def __init__(self, host, port, user, database, password):
        self.host = host
        self.port = port
        self.user = user
        self.database = database
        self.password = password
        self.connection = None

    async def connect(self):
        self.connection = await asyncpg.connect(host=self.host, port=self.port, user=self.user, database=self.database, password=self.password)
        print('Succesful CONNECTION!')

    async def select_query(self, query, *args):
        if not self.connection:
            await self.connect()
        async with self.connection.transaction():
            result = await self.connection.fetch(query, *args)
        return result
    
    async def select_one(self, query, *args):
        if not self.connection:
            await self.connect()
        async with self.connection.transaction():
            result = await self.connection.fetchrow(query, *args)
        return result

    async def exec_query(self, query, *args):
        if not self.connection:
            await self.connect()
        async with self.connection.transaction():
            await self.connection.execute(query, *args)

    async def insert_returning(self, query, *args):
        if not self.connection:
            await self.connect()
        async with self.connection.transaction():
            result = await self.connection.fetchval(query, *args)
            return result

    async def close_connection(self):
        if self.connection:
            await self.connection.close()


    
