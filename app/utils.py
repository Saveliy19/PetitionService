import os
from app.db import DataBase

from app.config import host, port, user, database, password, PHOTOS_DIRECTORY

db = DataBase(host, port, user, database, password)

# метод для создания новой петиции в базе
async def add_new_petition(*args):
        query = '''INSERT INTO PETITION (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_ID, LATITUDE, LONGITUDE, HEADER) 
                   VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING ID;'''
        petition_id = await db.insert_returning(query, *args)
        print(petition_id)
        return petition_id

# метод для обновления статуса имеющейся петиции
async def update_status_of_petition_by_id(*args):
        query = '''UPDATE PETITION
                   SET PETITION_STATUS = $1
                   WHERE ID = $2;'''
        await db.exec_query(query, *args)

# метод для лайка петиции или его отмены
async def like_petition_by_id(*args):
        query = '''SELECT * FROM LIKES WHERE PETITION_ID = $1 AND USER_ID = $2;'''
        existing_like = await db.select_one(query, *args)

        if not existing_like:
                query = '''INSERT INTO LIKES (PETITION_ID, USER_ID) VALUES ($1, $2);'''
                await db.exec_query(query, *args)
        else:
                query = '''DELETE FROM LIKES WHERE PETITION_ID = $1 AND USER_ID = $2;'''
                await db.exec_query(query, *args)

# метод для получения ID и заголовка заявки по айди пользователя
async def get_petitions_by_user_id(*args):
        query = '''SELECT ID, HEADER FROM PETITION WHERE PETITIONER_ID = $1;'''
        result = await db.select_query(query, *args)
        return result

# метод для получения полной информации по заявке по ее айди
async def get_full_info_by_petiton_id(*args):
        query = '''SELECT * FROM PETITION WHERE ID = $1;'''
        result = await db.select_one(query, *args)
        print(result)
        return result

# метод для получения количества лайков на петиции по ее айди
async def count_likes_by_petition_id(*args):
        query = '''SELECT COUNT(*) FROM LIKES WHERE PETITION_ID = $1;'''
        result = int((await db.select_one(query, *args))["count"])
        print(result)
        return result

async def add_photos_to_petition(petition_id, files):
        pass