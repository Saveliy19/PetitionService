import asyncio

from app.database import db

from app.schemas import (FullStatistics, RegionForDetailedAnalysis, SubjectForBriefAnalysis,
                         BriefAnalysis, Petition)

class StatisticsManager:
    def __init__(self, db):
        self.db = db
            
    async def _get_petition_count_per_status_by_period(self, region, start_time, end_time, is_initiative, city):
        # получаем количество жалоб/инициатив на статус за период в указанном городе
        if city != '': city_str = 'AND CITY_NAME = $5'
        else: city_str =''
        query = f'''
                SELECT PETITION_STATUS, COUNT(*) FROM PETITION
                WHERE IS_INITIATIVE = $4
                AND (SUBMISSION_TIME BETWEEN $2 AND $3)
                AND REGION = $1 {city_str}
                GROUP BY PETITION_STATUS;
                '''
        if city != '':
            return await self.db.select_query(query, region, start_time, end_time, is_initiative, city)
        return await self.db.select_query(query, region, start_time, end_time, is_initiative)
       
    
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
    

    # самые популярные жалобы или инициативы в указанном субъекте
    async def _get_most_popular_petitions(self, region, is_initiative, start_time, end_time, rows_count, city):
        city_str = 'AND CITY_NAME = $6' if city else ''

        query = f'''
                SELECT P.ID, P.HEADER
                , P.CATEGORY 
                , TO_CHAR(P.SUBMISSION_TIME,'YYYY-MM-DD HH24:MI:SS') as date
                , COUNT(L.ID) AS LIKE_COUNT
                FROM PETITION P
                LEFT JOIN LIKES L ON P.ID = L.PETITION_ID
                WHERE P.IS_INITIATIVE = $2
                AND REGION = $1 {city_str}
                AND (SUBMISSION_TIME BETWEEN $3 AND $4)
                GROUP BY P.ID
                ORDER BY LIKE_COUNT DESC
                LIMIT $5;
                '''
        
        if city != '':
            result = await self.db.select_query(query, region, is_initiative, start_time, end_time, rows_count, city)
        else:
            result = await self.db.select_query(query, region, is_initiative, start_time, end_time, rows_count)
        
        result = [Petition(
                id=record["id"],
                header=record["header"],
                category=record["category"],
                date=record["date"],
                like_count=record["like_count"])
                for record in result]
        return result
    
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
    
    async def get_brief_subject_analysis(self, subject: SubjectForBriefAnalysis):
        (
        most_popular_city_initiatives # 3 самых популярных инициативы в городе
        ,most_popular_city_complaints # 3 самых популярных жалобы в городе
        ,most_popular_region_initiatives # 3 самых популярных инициативы в регионе
        ,most_popular_region_complaints # 3 самых популярных жалобы в регионе
        ,city_complaints_count_per_status # количество жалоб на статус в городе
        ,city_initiatives_count_per_status # количество инициатив на статус в городе
        ,region_complaints_count_per_status # количетсво жалоб на статусе в регионе
        ,region_initiatives_count_per_status # количество инициатив на статус в регионе
        ) = await asyncio.gather(
        self._get_most_popular_petitions(subject.region, True, subject.start_time, subject.end_time, 3, subject.name),
        self._get_most_popular_petitions(subject.region, False, subject.start_time, subject.end_time, 3, subject.name),
        self._get_most_popular_petitions(subject.region, True, subject.start_time, subject.end_time, 3, ''),
        self._get_most_popular_petitions(subject.region, False, subject.start_time, subject.end_time, 3, ''),
        self._get_petition_count_per_status_by_period(subject.region, subject.start_time, subject.end_time, False, subject.name),
        self._get_petition_count_per_status_by_period(subject.region, subject.start_time, subject.end_time, True, subject.name),
        self._get_petition_count_per_status_by_period(subject.region, subject.start_time, subject.end_time, False, ''),
        self._get_petition_count_per_status_by_period(subject.region, subject.start_time, subject.end_time, True, ''),
        )
        
        return BriefAnalysis (
        most_popular_city_complaints=most_popular_city_complaints,
        most_popular_city_initiatives=most_popular_city_initiatives,
        most_popular_region_complaints=most_popular_region_complaints,
        most_popular_region_initiatives=most_popular_region_initiatives,
        city_complaints_count_per_status={record["petition_status"]: record["count"] for record in city_complaints_count_per_status},
        city_initiatives_count_per_status={record["petition_status"]: record["count"] for record in city_initiatives_count_per_status},
        region_complaints_count_per_status={record["petition_status"]: record["count"] for record in region_complaints_count_per_status},
        region_initiatives_count_per_status={record["petition_status"]: record["count"] for record in region_initiatives_count_per_status}
        )
    
    async def get_full_statistics(self, region: RegionForDetailedAnalysis):

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
        self._get_city_petitions_count_per_category(region.region_name, region.city_name, region.start_time, region.end_time, False),
        self._get_city_petitions_count_per_category(region.region_name, region.city_name, region.start_time, region.end_time, True),
        self._get_most_popular_petitions(region.region_name, True, region.start_time, region.end_time, region.rows_count, region.city_name),
        self._get_most_popular_petitions(region.region_name, False, region.start_time, region.end_time, region.rows_count, region.city_name),
        self._get_avg_region_petitions_count(region.region_name, region.start_time, region.end_time, False),
        self._get_avg_region_petitions_count(region.region_name, region.start_time, region.end_time, True),
        self._get_petitions_count_per_day(region.city_name, region.start_time, region.end_time, True, region.region_name),
        self._get_petitions_count_per_day(region.city_name, region.start_time, region.end_time, False, region.region_name)
        )

        return FullStatistics(
                complaints_count_per_category_city={record["category"]: record["count_per_category"] for record in cpc_city},
                initiatives_count_per_category_city={record["category"]: record["count_per_category"] for record in init_cpc_city},
                avg_complaints_count_per_category_region={record["category"]: record["count_per_category"] for record in cpc_reg},
                avg_initiatives_count_per_category_region={record["category"]: record["count_per_category"] for record in init_cpc_reg},
                city_initiatives_count_per_day={record["day"].strftime("%d-%m-%Y %H:%M:%S"): record["count"] for record in icpd},
                city_complaints_count_per_day={record["day"].strftime("%d-%m-%Y %H:%M:%S"): record["count"] for record in ccpd},
                most_popular_city_complaints=mpc_city,
                most_popular_city_initiatives=mpi_city
                )
    
statistics_manager = StatisticsManager(db)