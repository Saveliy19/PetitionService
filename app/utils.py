import os
from app.db import DataBase

from app.config import host, port, user, database, password, PHOTOS_DIRECTORY

import asyncio

db = DataBase(host, port, user, database, password)

# метод для создания новой петиции в базе
async def add_new_petition(*args):
        query = '''INSERT INTO PETITION (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_ID, LATITUDE, LONGITUDE, HEADER, REGION, CITY_NAME) 
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING ID;'''
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

# метод для получения списка всех заявок в указанном городе
async def get_petitions_by_city(*args):
        query = '''SELECT ID, HEADER FROM PETITION WHERE REGION = $1 AND CITY_NAME = $2;'''
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


async def get_brief_subject_analysis(*args):
        query1 = f'''SELECT IS_INITIATIVE, COUNT(*) 
                     FROM PETITION
                     WHERE SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                     AND {args[0]} = '{args[1]}'
                     GROUP BY IS_INITIATIVE;'''
        query2 = f'''SELECT CATEGORY FROM PETITION
                     WHERE SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                     AND IS_INITIATIVE = 'f'
                     AND {args[0]} = '{args[1]}'
                     GROUP BY CATEGORY
                     ORDER BY COUNT(*) DESC
                     LIMIT 1;'''
        query3 = f'''SELECT ROUND((COUNT(CASE WHEN PETITION_STATUS = 'Решена' THEN 1 END)::numeric / COUNT(*)) * 100, 1) AS percent_resolved
                    FROM PETITION
                    WHERE IS_INITIATIVE = 'f'
                    AND SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                    AND {args[0]} = '{args[1]}';'''
        query4 = f'''SELECT ROUND((COUNT(CASE WHEN PETITION_STATUS = 'Одобрена' THEN 1 END)::numeric / COUNT(*)) * 100, 1) AS percent_resolved
                    FROM PETITION
                    WHERE IS_INITIATIVE = 't'
                    AND SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                    AND {args[0]} = '{args[1]}';'''
        query5 = f'''SELECT CATEGORY FROM PETITION
                     WHERE SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                     AND IS_INITIATIVE = 't'
                     AND {args[0]} = '{args[1]}'
                     GROUP BY CATEGORY
                     ORDER BY COUNT(*) DESC
                     LIMIT 1;'''
        petitions, most_popular_petition, resolved_percent, accepted_percent, most_popular_initiative = await asyncio.gather(db.select_query(query1), 
                                                                                                                             db.select_query(query2), 
                                                                                                                             db.select_query(query3), 
                                                                                                                             db.select_query(query4),
                                                                                                                             db.select_query(query5))
        return {"petitions_count" : petitions[0]["count"], 
                "initiatives_count": petitions[1]["count"], 
                "most_popular_petition": most_popular_petition[0]["category"], 
                "most_popular_initiative": most_popular_initiative[0]["category"], 
                "solved_percent": float(resolved_percent[0]["percent_resolved"]),
                "accepted_percent": float(accepted_percent[0]["percent_resolved"])}

async def add_photos_to_petition(petition_id, files):
        pass