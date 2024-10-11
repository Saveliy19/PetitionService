import os
from app.config import settings
import base64

from app.logger import logger

import asyncio

PHOTOS_DIRECTORY = settings.photos_directory

from app.database import db

from app.schemas import (
                        PetitionStatus, NewPetition, Like, PetitionWithHeader, 
                        City, CityWithType, AdminPetition, Comment, PetitionToGetData,
                        PetitionData
                       )

class PetitionManager:
        def __init__(self, db):
                self.db = db

        async def check_existance(self, petition_id: int):
                try:
                        petition_query = '''SELECT ID FROM PETITIONS WHERE ID = $1;'''
                        existing_petition = await self.db.select_one(petition_query, petition_id)
                        if existing_petition is None:
                                return False
                        return True
                except Exception as e:
                        logger.error(f"Ошибка при проверке существования петиции id {petition_id}", exc_info=e)
                        raise e

        async def add_new_petition(self, petition: NewPetition):
                try:
                        query = '''INSERT INTO PETITION 
                        (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_EMAIL, ADDRESS, HEADER, REGION, CITY_NAME) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING ID;'''
                        petition_id = await self.db.insert_returning(query, petition.is_initiative,
                                                                        petition.category,
                                                                        petition.petition_description,
                                                                        petition.petitioner_email,
                                                                        petition.address,
                                                                        petition.header,
                                                                        petition.region,
                                                                        petition.city_name)
                        return {"petition_id": f"{petition_id}"}
                except Exception as e:
                        logger.error("Ошибка при создании петиции", exc_info=e)
                        raise e
        
        async def get_full_data(self, petition: PetitionToGetData):
                queries = [asyncio.create_task(self.get_full_petition_info(petition.id)),
                           asyncio.create_task(self.get_petition_comments(petition.id)),
                           asyncio.create_task(self.get_petition_photos(petition.id))]
                done, pending = await asyncio.wait(queries, return_when=asyncio.FIRST_EXCEPTION)

                if len(done) != 3:
                        for pending_task in pending:
                                pending_task.cancel()
                        for task in done:
                                if task.exception is not None:
                                        logger.error(f"Ошибка при получении данных заявки id {petition.id}", exc_info=task.exception())
                                        raise task.exception()

                else:
                        for task in done:
                                if task is queries[1]:
                                        info = task.result()
                                elif task is queries[2]:
                                        output_comments = task.result()
                                else:
                                        photos = task.result()

                return PetitionData(id = info["id"], 
                        header = info["header"], 
                        is_initiative = info["is_initiative"], 
                        category = info["category"],
                        description = info["petition_description"],
                        status = info["petition_status"],
                        petitioner_email = info["petitioner_email"],
                        submission_time = info["submission_time"].strftime('%d.%m.%Y %H:%M'),
                        address = info["address"],
                        region = info["region"],
                        city_name = info["city_name"],
                        likes_count = info["likes_count"],
                        comments = output_comments,
                        photos = photos)
        
        async def update_petition_status(self, petition: PetitionStatus):
                query1 = f'''UPDATE PETITION
                             SET PETITION_STATUS = $1
                             WHERE ID = $2;'''
                query2 = f'''INSERT INTO COMMENTS (PETITION_ID, USER_ID, COMMENT_DESCRIPTION)
                             VALUES ($1, $2, $3);'''
                try:
                        await self.db.exec_many_query({
                        query1: [petition.status, petition.id],
                        query2: [petition.id, petition.admin_id, petition.comment]
                        })
                        return True
                except:
                        return False
        
        # получение списка пользователей, которые подписались под заявкой + сам заявитель
        async def get_petitioners_email(self, petition: PetitionStatus):
                query = f'''
                        SELECT PETITIONER_EMAIL AS email
                        FROM PETITION
                        WHERE ID = $1

                        UNION

                        SELECT USER_EMAIL AS email
                        FROM PETITION 
                        JOIN LIKES ON PETITION.ID = LIKES.PETITION_ID
                        WHERE PETITION.ID = $1;
                '''
                results = await self.db.select_query(query, petition.id)
                emails = [item["email"] for item in results]
                return {"petitioner_emails": emails}
        
        # проверяем лайк пользователя на записи
        async def check_user_like(self, like: Like):
                query = '''SELECT * FROM LIKES WHERE PETITION_ID = $1 AND USER_EMAIL = $2;'''
                existing_like = await self.db.select_one(query, like.petition_id, like.user_email)
                if not existing_like:
                        return False
                return True
        
        async def _delete_like(self, like: Like):
                query = '''DELETE FROM LIKES WHERE PETITION_ID = $1 AND USER_EMAIL = $2;'''
                await self.db.exec_query(query, like.petition_id, like.user_email)

        async def _insert_like(self, like: Like):
                query = '''INSERT INTO LIKES (PETITION_ID, USER_EMAIL) VALUES ($1, $2);'''
                await self.db.exec_query(query, like.petition_id, like.user_email)

        # установка лайка на петицию
        async def like_petition(self, like: Like):
                existing_like = self.check_user_like(like)

                if not existing_like:
                        self._insert_like(like)
                else:
                        self._delete_like(like)

        # получаем список петиций пользователя по его email
        async def get_petitions_by_email(self, email):
                query = '''SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS,
                         p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                        FROM petition p
                        LEFT JOIN likes l ON p.ID = l.PETITION_ID
                        WHERE p.PETITIONER_EMAIL = $1 
                        GROUP BY p.ID;'''
                result = await self.db.select_query(query, email)
                petitions = [PetitionWithHeader(id=r["id"], 
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes = r["likes_count"]) for r in result]
                return petitions

        # проверка соответствия города петиции
        async def check_city_by_petition_id(self, petition: PetitionStatus):
                query = '''SELECT ($2, $3) IN
                         (SELECT REGION, CITY_NAME FROM PETITION WHERE id=$1)
                           as result;'''
                result = await self.db.select_query(query, petition.id, petition.admin_region, petition.admin_city)
                return result[0]["result"]

        # получаем список петиций и краткую информацию о них в указанном городе
        async def get_city_petitions(self, city: CityWithType):
                query = '''SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.REGION = $1 
                AND p.CITY_NAME = $2 
                AND p.PETITION_STATUS != 'На модерации'
                AND p.IS_INITIATIVE = $3
                GROUP BY p.ID;
                '''
                result = await self.db.select_query(query, city.region, city.name, city.is_initiative)
                petitions = [PetitionWithHeader(id=r["id"], 
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes=r["likes_count"]) for r in result]
                return petitions

        # получаем список петиций с информацией о них в указанном городе, включая со статусом на модерации (доступно только админам)
        async def get_admin_petitions(self, city: City):
                query = '''SELECT p.ID, p.IS_INITIATIVE, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.REGION = $1 
                AND p.CITY_NAME = $2
                GROUP BY p.ID;'''
                result = await self.db.select_query(query, city.region, city.name)
                petitions = [AdminPetition(id=r["id"],
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes=r["likes_count"],
                                        type = 'Жалоба' if r["is_initiative"] == False else 'Инициатива') for r in result]
                return result
        
        # получаем полную информацию о петиции
        async def get_full_petition_info(self, *args):
                query = '''SELECT p.*, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.ID = $1
                GROUP BY p.ID;'''
                result = await self.db.select_one(query, *args)
                return result
        
        # получаем комментарии к петиции
        async def get_petition_comments(self, petition_id):
                query = '''SELECT SUBMISSION_TIME, COMMENT_DESCRIPTION FROM COMMENTS WHERE PETITION_ID = $1;'''
                comments = await self.db.select_query(query, petition_id)
                output_comments = [Comment(date=c["submission_time"].strftime('%d.%m.%Y %H:%M'), data=c["comment_description"]) for c in comments]
                return output_comments
        
        # добавляем фотографии петиции
        async def add_petition_photos(self, petition_id, photos):
                folder_path = PHOTOS_DIRECTORY + f"{petition_id}"
                os.mkdir(folder_path)
                for p in photos:
                        with open(PHOTOS_DIRECTORY + f'{petition_id}/{p.filename}', 'wb') as f:
                                f.write(base64.b64decode(p.content))

                query = '''INSERT INTO PHOTO_FOLDER (PETITION_ID, FOLDER_PATH) VALUES ($1, $2);'''
                await self.db.exec_query(query, petition_id, folder_path)

        # получаем фотографии петиции
        async def get_petition_photos(self, petition_id):
                photos = []
                query = f'''SELECT FOLDER_PATH FROM PHOTO_FOLDER WHERE PETITION_ID = $1;'''
                folder_path = (await self.db.select_one(query, petition_id))["folder_path"]
                for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        photos.append('http://127.0.0.1:8002/images/' +file_path)
                return photos
        
petition_manager = PetitionManager(db)