import asyncio

from app.database import db

class StatisticsManager:
    def __init__(self, db):
        self.db = db
    
    async def _get_most_popular_city_petition_by_period(self, region_name, city_name, period, is_initiative, rows):
        # получаем самую популярную категорию жалоб/иниициатив в указанном городе за определенный период
        query = '''
                SELECT CATEGORY, count(*) FROM PETITION
                WHERE SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '{period}'
                AND IS_INITIATIVE = $3
                AND REGION = $1 AND CITY_NAME = $2
                GROUP BY CATEGORY
                ORDER BY COUNT(*) DESC
                LIMIT $4;
                '''
        result = {record["category"]: record["count"] for record in await self.db.select_query(query, region_name, city_name, is_initiative, rows)}
        return result
        
    async def _get_most_popular_region_petition_by_period(self, region, period, is_initiative, rows):
        # получаем самую популярную категорию жалоб/инициатив в указанном РЕГИОНЕ за определенный период
        query = '''
                SELECT CATEGORY, count(*) FROM PETITION
                WHERE SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '{period}'
                AND IS_INITIATIVE = $2
                AND REGION = $1
                GROUP BY CATEGORY
                ORDER BY COUNT(*) DESC
                LIMIT $3;
                '''
        result = {record["category"]: record["count"] for record in await self.db.select_query(query, region, is_initiative, rows)}
        return result
            
    async def _get_city_petition_count_per_status_by_period(self, region, city, period, is_initiative):
        # получаем количество жалоб/инициатив на статус за период в указанном городе
        query = '''
                SELECT PETITION_STATUS, COUNT(*) FROM PETITION
                WHERE IS_INITIATIVE = $3
                AND SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '{period}'
                AND REGION = $1 AND CITY_NAME = $2
                GROUP BY PETITION_STATUS;
                '''
        result = {record["petition_status"]: record["count"] for record in await self.db.select_query(query, region, city, is_initiative)}
        return result

    async def _get_region_petition_count_per_status_by_period(self, region, period, is_initiative):
        # получаем количество жалоб/инициатив на статус за период в указанном РЕГИОНЕ
        query = '''
                SELECT PETITION_STATUS, COUNT(*) FROM PETITION
                WHERE IS_INITIATIVE = $2
                AND SUBMISSION_TIME >= CURRENT_DATE - INTERVAL '{period}'
                AND REGION = $1
                GROUP BY PETITION_STATUS;
                '''
        result = {record["petition_status"]: record["count"] for record in await self.db.select_query(query, region, is_initiative)}
        return result

    async def _get_brief_subject_analysis(self, region_name, city_name, period):
        interval_mapping = {
                "year": "1 year",
                "month": "1 month",
                "day": "1 day",
                "week": "1 week"
        }
        period = interval_mapping[period]
        (
        most_popular_city_initiatives
        ,most_popular_city_complaints
        ,most_popular_region_initiatives
        ,most_popular_region_complaints
        ,city_complaints_count_per_status
        ,city_initiatives_count_per_status
        ,region_complaints_count_per_status
        ,region_initiatives_count_per_status
        ) = await asyncio.gather(
        self._get_most_popular_city_petition_by_period(region_name, city_name, period, True, 3)
        ,self._get_most_popular_city_petition_by_period(region_name, city_name, period, False, 3)
        ,self._get_most_popular_region_petition_by_period(region_name, period, True, 3)
        ,self._get_most_popular_region_petition_by_period(region_name, period, False, 3)
        ,self._get_city_petition_count_per_status_by_period(region_name, city_name, period, False)
        ,self._get_city_petition_count_per_status_by_period(region_name, city_name, period, True)
        ,self._get_region_petition_count_per_status_by_period(region_name, period, False)
        ,self._get_region_petition_count_per_status_by_period(region_name, period, True)
        )
        

        return {"most_popular_city_initiatives": most_popular_city_initiatives
                ,"most_popular_city_complaints": most_popular_city_complaints
                ,"city_initiatives_count_per_status": city_initiatives_count_per_status
                ,"city_complaints_count_per_status": city_complaints_count_per_status
                ,"most_popular_region_initiatives": most_popular_region_initiatives
                ,"most_popular_region_complaints": most_popular_region_complaints
                ,"region_initiatives_count_per_status": region_initiatives_count_per_status
                ,"region_complaints_count_per_status": region_complaints_count_per_status
                }
    
    # получени количества петиций на категорию в городе
    async def _get_city_petitions_count_per_category(self, region, city, start_time, end_time, is_initiative):
        query = '''
                SELECT CATEGORY, COUNT(*) AS COUNT_PER_CATEGORY
                FROM PETITION
                WHERE REGION = $1 AND CITY_NAME = $2
                AND (SUBMISSION_TIME BETWEEN $3 AND $4)
                AND IS_INITIATIVE = $5
                GROUP BY CATEGORY;
                '''
        return await self.db.select_query(query, region, city, start_time, end_time, is_initiative)
    
    # самые популярные жалобы или инициативы в указанном городе
    async def _get_most_popular_city_petitions(self, region, city, start_time, end_time, rows_count, is_initiative):
        query = '''
                SELECT P.ID, P.HEADER
                , P.CATEGORY 
                , TO_CHAR(P.SUBMISSION_TIME,'YYYY-MM-DD HH24:MI:SS')
                , COUNT(L.ID) AS LIKE_COUNT
                FROM PETITION P
                LEFT JOIN LIKES L ON P.ID = L.PETITION_ID
                WHERE P.IS_INITIATIVE = $6
                AND REGION = $1 AND CITY_NAME = $2
                AND (SUBMISSION_TIME BETWEEN $3 AND $4)
                GROUP BY P.ID
                ORDER BY LIKE_COUNT DESC
                LIMIT $5;
                '''
        return await self.db.select_query(query, region, city, start_time, end_time, rows_count, is_initiative)
    
    # среднее количество петиций на категорию в регионе
    async def _get_avg_region_petitions_count(self, region, start_time, end_time, is_initiative):
        query = '''
                WITH CITY_COUNT AS (
                SELECT COUNT(DISTINCT CITY_NAME) AS CITY_COUNT
                FROM PETITION
                WHERE REGION = $1
                )

                SELECT CATEGORY, CAST(COUNT(*) AS FLOAT) / (SELECT CITY_COUNT FROM CITY_COUNT) AS COUNT_PER_CATEGORY
                FROM PETITION
                WHERE REGION = $1
                AND (SUBMISSION_TIME BETWEEN $2 AND $3)
                AND IS_INITIATIVE = $4
                GROUP BY CATEGORY;
                '''
        return await self.db.select_query(query, region, start_time, end_time, is_initiative)
    
    # получение количества петиций в день за указанный период в указанном городе
    async def _get_petitions_count_per_day(self, city, start_time, end_time, is_initiative, region):
        query = '''
                SELECT DATE(dates.d) AS DAY, COUNT(PETITION.SUBMISSION_TIME) AS COUNT
                FROM GENERATE_SERIES($2::TIMESTAMP, $3::TIMESTAMP, '1 day') AS dates(d)
                LEFT JOIN PETITION ON DATE(PETITION.SUBMISSION_TIME) = DATE(dates.d)
                AND PETITION.IS_INITIATIVE = $4
                AND PETITION.REGION = $5
                AND PETITION.CITY_NAME = $1
                WHERE DATE(dates.d) BETWEEN $2 AND $3
                GROUP BY DATE(dates.d)
                ORDER BY DAY;
                '''
        return await self.db.select_query(query, city, start_time, end_time, is_initiative, region)
    
    async def get_full_statistics(self, region_name, city_name, start_time, end_time, rows_count):

        (
        cpc_city, # количетство жалоб на категорию за указанный период в городе
        init_cpc_city, # количество инициатив на категорию за указанный период в городе
        mpi_city, # самые популярные инициативы в городе
        mpc_city, # сымые популярные жалобы в городе
        cpc_reg, # среднее количество жалоб на категорию в регионе
        init_cpc_reg, # среднее количество инициатив на категорию в регионе
        icpd, # количество инициатив в день за указанный период
        ccpd # количество жалоб в день за указанный период
        ) = await asyncio.gather(
        self._get_city_petitions_count_per_category(region_name, city_name, start_time, end_time, False),
        self._get_city_petitions_count_per_category(region_name, city_name, start_time, end_time, True),
        self._get_most_popular_city_petitions(region_name, city_name, start_time, end_time, rows_count, True),
        self._get_most_popular_city_petitions(region_name, city_name, start_time, end_time, rows_count, False),
        self._get_avg_region_petitions_count(region_name, start_time, end_time, False),
        self._get_avg_region_petitions_count(region_name, start_time, end_time, True),
        self._get_petitions_count_per_day(city_name, start_time, end_time, True, region_name),
        self._get_petitions_count_per_day(city_name, start_time, end_time, False, region_name)
        )
            
        return {"complaints_count_per_category_city": {record["category"]: record["count_per_category"] for record in cpc_city},
                "avg_complaints_count_per_category_region": {record["category"]: record["count_per_category"] for record in cpc_reg},
                "avg_initiatives_count_per_category_region": {record["category"]: record["count_per_category"] for record in init_cpc_reg},
                "initiatives_count_per_category_city": {record["category"]: record["count_per_category"] for record in init_cpc_city},
                "city_initiatives_count_per_day": {record["day"].strftime("%d-%m-%Y %H:%M:%S"): record["count"] for record in icpd},
                "city_complaints_count_per_day": {record["day"].strftime("%d-%m-%Y %H:%M:%S"): record["count"] for record in ccpd},
                "most_popular_city_initiatives": [dict(record) for record in mpi_city],
                "most_popular_city_complaints": [dict(record) for record in mpc_city]}
    
statistics_manager = StatisticsManager(db)