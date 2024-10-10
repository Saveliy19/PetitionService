import asyncio
import asyncpg
import random
from app import settings

cities = ['Emva', 'Syktyvkar', 'Ukhta', 'Sosnogorsk']
region = 'Komi'
category = ['Дороги и транспорт', 'Безопасность', 'Благоустройство', 'Развлечения', 'Культура', 'ЖКХ', 'Медицина']

async def generate_petitions(pool, n):
    rows_count_query = '''SELECT COUNT(*) FROM PETITION;'''
    async with pool.acquire() as connection:
        row = await connection.fetchrow(rows_count_query)  # Выполняем запрос
        count = row[0] if row is not None else 0

    query = '''
        INSERT INTO PETITION (
        HEADER, 
        IS_INITIATIVE, 
        CATEGORY, 
        PETITION_DESCRIPTION, 
        PETITIONER_EMAIL, 
        ADDRESS, 
        REGION, 
        CITY_NAME
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8        
        );
    '''
    data = []
    for i in range(count + 1, count + n + 1):
        data.append(
            (f'Header{i}',
            random.choice([True, False]),  
            category[random.randint(0, len(category) - 1)],  
            f'Description{i}',
            f'user{i}@mail.com',
            f'Address{i}',
            region,
            cities[random.randint(0, len(cities) - 1)] )
        )
    
    async with pool.acquire() as connection:
        await connection.executemany(query, data)

async def generate_comments(pool, n):
    rows_count_query = '''SELECT COUNT(*) FROM COMMENTS;'''
    async with pool.acquire() as connection:
        row = await connection.fetchrow(rows_count_query)  # Выполняем запрос
        count = row[0] if row is not None else 0
    query = '''
        INSERT INTO COMMENTS (
        PETITION_ID,
        USER_ID,
        COMMENT_DESCRIPTION
        ) VALUES (
            $1, $2, $3
        );
    '''
    data = []
    for i in range(count + 1, count + n + 1):
        data.append(
            (i,
            random.randint(0, 450000),  
            f'Comment_description {i}')  
        )
    async with pool.acquire() as connection:
        await connection.executemany(query, data)

async def generate_likes(pool, n):
    rows_count_query = '''SELECT COUNT(*) FROM LIKES;'''
    async with pool.acquire() as connection:
        row = await connection.fetchrow(rows_count_query)  # Выполняем запрос
        count = row[0] if row is not None else 0
    query = '''
        INSERT INTO LIKES (
        USER_EMAIL,
        PETITION_ID
        ) VALUES (
        $1, $2);
    '''
    data = []
    for i in range(count + 1, count + n - 5):
        data.append((f'user{random.randint(i + 1, i + 3)}@mail.com', i))
        data.append((f'user{random.randint(i + 4, i + 6)}@mail.com', i))

    
    async with pool.acquire() as connection:
        await connection.executemany(query, data)

async def seed_data(n):
    pool = await asyncpg.create_pool(settings.host,
                                    settings.port,
                                    settings.user,
                                    settings.database,
                                    settings.password,
                                    min_size=1,
                                    max_size=10)

    await generate_petitions(pool, n)
    await generate_comments(pool, n)
    await generate_likes(pool, n)

    await pool.close()

if __name__ == '__main__':
    n = 500000
    asyncio.run(seed_data(n))
