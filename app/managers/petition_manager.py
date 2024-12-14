from app.config import settings

from app import logger

import asyncio

from app.database import db

from .like_manager import LikeManager
from .media_manager import MediaManager

from app.schemas import (
    PetitionStatus, NewPetition, Like, PetitionWithHeader,
    City, CityWithType, Comment, Id,
    PetitionData, Petitioners, AdminPetition
    )


class PetitionManager:
    def __init__(self, db):
        self.db = db
        self.like_manager = LikeManager(db)
        self.media_manager = MediaManager(db, settings.photos_directory)

    async def check_existance(self, petition_id: int):
        try:
            petition_query = '''SELECT ID FROM PETITION WHERE ID = $1;'''
            existing_petition = await self.db.select_one(petition_query, petition_id)
            if existing_petition is None:
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке существования петиции id {petition_id}", exc_info=e)
            raise

    async def add_new_petition(self, petition: NewPetition):
        try:
            query = '''INSERT INTO PETITION
            (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_EMAIL, ADDRESS, HEADER, REGION, CITY_NAME)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING ID;'''
            petition_id = await self.db.insert_returning(
                query, petition.is_initiative,
                petition.category,
                petition.petition_description,
                petition.petitioner_email,
                petition.address,
                petition.header,
                petition.region,
                petition.city_name
                )
            return Id(id=petition_id)

        except Exception as e:
            logger.error("Ошибка при создании петиции", exc_info=e)
            raise e

    # получаем полную информацию о петиции
    async def get_full_petition_info(self, *args):
        query = '''SELECT p.*, COUNT(l.petition_id) AS likes_count
        FROM petition p
        LEFT JOIN likes l ON p.ID = l.PETITION_ID
        WHERE p.ID = $1
        GROUP BY p.ID;'''
        result = await self.db.select_one(query, *args)
        return result

    async def get_full_data(self, petition_id: int):
        info, output_comments, photos = await asyncio.gather(
            self.get_full_petition_info(petition_id),
            self.get_petition_comments(petition_id),
            self.get_petition_photos(petition_id))

        return PetitionData(
            id=info["id"],
            header=info["header"],
            is_initiative=info["is_initiative"],
            category=info["category"],
            description=info["petition_description"],
            status=info["petition_status"],
            petitioner_email=info["petitioner_email"],
            submission_time=info["submission_time"].strftime('%d.%m.%Y %H:%M'),
            address=info["address"],
            region=info["region"],
            city_name=info["city_name"],
            likes_count=info["likes_count"],
            comments=output_comments,
            photos=photos
            )

    async def update_petition_status(self, petition: PetitionStatus):
        query1 = '''UPDATE PETITION
                SET PETITION_STATUS = $1
                WHERE ID = $2;'''
        query2 = '''INSERT INTO COMMENTS (PETITION_ID, USER_ID, COMMENT_DESCRIPTION)
                VALUES ($1, $2, $3);'''
        try:
            await self.db.exec_many_query(
                {query1: [petition.status, id],
                 query2: [id, petition.admin_id, petition.comment]}
                )
            return True
        except Exception:
            return False

    # получение списка пользователей, которые подписались под заявкой + сам заявитель
    async def get_petitioners_email(self, petition: PetitionStatus):
        query = '''
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
        return Petitioners(petitioners_emails=[item["email"] for item in results])

    async def check_user_like(self, like: Like):
        return await self.like_manager.check_user_like(like)

    async def like_petition(self, like: Like):
        return await self.like_manager.like_petition(like)

    async def dislike_petition(self, like: Like):
        return await self.like_manager.delete_like(like)

    # получаем список петиций пользователя по его email
    async def get_petitions_by_email(self, email):
        query = '''SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS,
                        p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.PETITIONER_EMAIL = $1
                GROUP BY p.ID;'''
        result = await self.db.select_query(query, email)
        petitions = [
            PetitionWithHeader(
                id=r["id"],
                header=r["header"],
                status=r["petition_status"],
                address=r["address"],
                date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                likes=r["likes_count"]) for r in result
            ]
        return petitions

    # проверка соответствия города петиции
    async def check_city_by_petition_id(self, petition: PetitionStatus):
        query = '''SELECT ($2, $3) IN
                        (SELECT REGION, CITY_NAME FROM PETITION WHERE id=$1)
                        as result;'''
        result = await self.db.select_one(query, petition.id, petition.admin_region, petition.admin_city)
        return result["result"]

    # получаем список петиций и краткую информацию о них в указанном городе
    async def get_city_petitions(self, city: CityWithType):
        query = '''
        SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
        FROM petition p
        LEFT JOIN likes l ON p.ID = l.PETITION_ID
        WHERE p.REGION = $1
        AND p.CITY_NAME = $2
        AND p.PETITION_STATUS != 'На модерации'
        AND p.IS_INITIATIVE = $3
        GROUP BY p.ID
        LIMIT $4
        OFFSET $5;
        '''
        result = await self.db.select_query(query, city.region, city.name, city.is_initiative, city.limit, city.offset)
        petitions = [
            PetitionWithHeader(
                id=r["id"],
                header=r["header"],
                status=r["petition_status"],
                address=r["address"],
                date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                likes=r["likes_count"]) for r in result
            ]
        return petitions

    # получаем список петиций с информацией о них в указанном городе, включая со статусом на модерации (доступно только админам)
    async def get_admin_petitions(self, city: City):
        query = '''SELECT p.ID
                ,p.IS_INITIATIVE
                ,p.HEADER
                ,p.PETITION_STATUS
                ,p.ADDRESS
                ,p.SUBMISSION_TIME
                ,COUNT(l.petition_id) AS likes_count
        FROM petition p
        LEFT JOIN likes l ON p.ID = l.PETITION_ID
        WHERE p.REGION = $1
        AND p.CITY_NAME = $2
        GROUP BY p.ID
        LIMIT $3
        OFFSET $4;'''
        result = await self.db.select_query(query, city.region, city.name, city.limit, city.offset)
        petitions = [
            AdminPetition(
                id=r["id"],
                header=r["header"],
                status=r["petition_status"],
                address=r["address"],
                date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                likes=r["likes_count"],
                type='Жалоба' if r["is_initiative"] is False else 'Инициатива') for r in result
            ]
        return petitions

    # получаем комментарии к петиции
    async def get_petition_comments(self, petition_id: int):
        query = '''SELECT SUBMISSION_TIME, COMMENT_DESCRIPTION FROM COMMENTS WHERE PETITION_ID = $1;'''
        comments = await self.db.select_query(query, petition_id)
        output_comments = [Comment(date=c["submission_time"].strftime('%d.%m.%Y %H:%M'), data=c["comment_description"]) for c in comments]
        return output_comments

    # добавляем фотографии петиции
    async def add_petition_photos(self, petition_id: int, petition: NewPetition):
        await self.media_manager.add_petition_photos(petition_id, petition)

    # получаем фотографии петиции
    async def get_petition_photos(self, petition_id: int):
        return await self.media_manager.get_petition_photos(petition_id)


petition_manager = PetitionManager(db)
