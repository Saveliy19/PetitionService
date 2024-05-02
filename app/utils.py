import os
from app.db import DataBase

from app.config import host, port, user, database, password, PHOTOS_DIRECTORY

db = DataBase(host, port, user, database, password)

async def add_new_petition(*args):
        query = '''INSERT INTO PETITION (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_ID, LATITUDE, LONGITUDE, HEADER) 
                   VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING ID;'''
        petition_id = await db.insert_returning(query, *args)
        print(petition_id)
        return petition_id


async def add_photos_to_petition(petition_id, files):
        pass