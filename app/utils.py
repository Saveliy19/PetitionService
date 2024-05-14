import os
from app.db import DataBase

from app.config import host, port, user, database, password, PHOTOS_DIRECTORY
import base64

import asyncio

db = DataBase(host, port, user, database, password)

# метод для создания новой петиции в базе
async def add_new_petition(*args):
        query = '''INSERT INTO PETITION (IS_INITIATIVE, CATEGORY, PETITION_DESCRIPTION, PETITIONER_EMAIL, ADDRESS, HEADER, REGION, CITY_NAME) 
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING ID;'''
        petition_id = await db.insert_returning(query, *args)
        print(petition_id)
        return petition_id

# метод для обновления статуса имеющейся петиции
async def update_status_of_petition_by_id(status, id, admin_id, comment):
        query1 = f'''UPDATE PETITION
                   SET PETITION_STATUS = '{status}'
                   WHERE ID = {id};'''
        query2 = f'''INSERT INTO COMMENTS (PETITION_ID, USER_ID, COMMENT_DESCRIPTION) VALUES ({id}, {admin_id}, '{comment}');'''
        result = await db.exec_many_query([query1, query2])
        return result

async def get_petitioner_email_by_petition_id(petition_id):
        query = f'''SELECT PETITIONER_EMAIL 
                    FROM PETITION
                    WHERE ID = {petition_id}'''
        email = await db.select_one(query)
        return email["petitioner_email"]

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
async def get_petitions_by_user_email(*args):
        query = '''SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.PETITIONER_EMAIL = $1 
                GROUP BY p.ID;'''
        result = await db.select_query(query, *args)
        return result

# метод для получения списка всех заявок в указанном городе
async def get_petitions_by_city(*args):
        query = '''SELECT p.ID, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.REGION = $1 
                AND p.CITY_NAME = $2 
                AND p.PETITION_STATUS != 'ожидает модерации'
                AND p.IS_INITIATIVE = $3
                GROUP BY p.ID;
                '''
        result = await db.select_query(query, *args)
        return result

# метод для получения списка всех заявок для администрирования
async def get_admin_petitions(*args):
        query = '''SELECT p.ID, p.IS_INITIATIVE, p.HEADER, p.PETITION_STATUS, p.ADDRESS, p.SUBMISSION_TIME, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.REGION = $1 
                AND p.CITY_NAME = $2
                GROUP BY p.ID;'''
        result = await db.select_query(query, *args)
        return result

# метод для получения полной информации по заявке по ее айди
async def get_full_info_by_petiton_id(*args):
        
        query = '''SELECT p.*, COUNT(l.petition_id) AS likes_count
                FROM petition p
                LEFT JOIN likes l ON p.ID = l.PETITION_ID
                WHERE p.ID = $1
                GROUP BY p.ID;'''
        result = await db.select_one(query, *args)
        print(result)
        return result

# метод для получения количества лайков на петиции по ее айди
async def get_comments_by_petition_id(*args):
        query = '''SELECT SUBMISSION_TIME, COMMENT_DESCRIPTION FROM COMMENTS WHERE PETITION_ID = $1;'''
        result = await db.select_query(query, *args)
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
        query3 = f'''SELECT ROUND((COUNT(CASE WHEN PETITION_STATUS = 'Решено' THEN 1 END)::numeric / COUNT(*)) * 100, 1) AS percent_resolved
                    FROM PETITION
                    WHERE IS_INITIATIVE = 'f'
                    AND SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '1 {args[2]}'
                    AND {args[0]} = '{args[1]}';'''
        query4 = f'''SELECT ROUND((COUNT(CASE WHEN PETITION_STATUS = 'Одобрено' THEN 1 END)::numeric / COUNT(*)) * 100, 1) AS percent_resolved
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

async def check_user_like(*args):
        query = '''SELECT * FROM LIKES WHERE PETITION_ID = $1 AND USER_ID = $2;'''
        existing_like = await db.select_one(query, *args)
        if not existing_like:
                return False
        return True

async def add_photos_to_petition(petition_id, photos):
        folder_path = PHOTOS_DIRECTORY + f"{petition_id}"
        os.mkdir(folder_path)
        for p in photos:
                with open(PHOTOS_DIRECTORY + f'{petition_id}/{p.filename}', 'wb') as f:
                        f.write(base64.b64decode(p.content))

        query = f'''INSERT INTO PHOTO_FOLDER (PETITION_ID, FOLDER_PATH) VALUES ({petition_id}, '{folder_path}');'''
        await db.exec_query(query)
        
async def get_photos_by_petition_id(petition_id):
        photos = []
        query = f'''SELECT FOLDER_PATH FROM PHOTO_FOLDER WHERE PETITION_ID = {petition_id};'''
        folder_path = (await db.select_one(query))["folder_path"]
        for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                photos.append('http://127.0.0.1:8002/images/' +file_path)
        return photos