from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse

import time

from app.schemas.models import SubjectForBriefAnalysis, RegionForDetailedAnalysis
from app.managers import statistics_manager

from app.logger import logger

statistics_router = APIRouter()

from fastapi_cache.decorator import cache

# маршрут для получения краткой аналитики по населенному пункту
@statistics_router.get("/brief/{region_name}/{city_name}", status_code=status.HTTP_200_OK)
@cache(expire=60*60)
async def get_brief_analysis(subject: SubjectForBriefAnalysis = Depends()):
    try:
        info = await statistics_manager.get_brief_subject_analysis(subject.region, subject.name, subject.period)
    except:
        logger.error("Ошибка при получении краткой статистики", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = info)


@statistics_router.get("/detailed/{region_name}/{city_name}", status_code=status.HTTP_200_OK)
@cache(expire=240)
async def get_detailed_analysis(subject: RegionForDetailedAnalysis = Depends()):
    time.sleep(10)
    try:
        info = await statistics_manager.get_full_statistics(subject.region_name, 
                                                            subject.city_name, 
                                                            subject.start_time, 
                                                            subject.end_time, 
                                                            subject.rows_count)
    except Exception as e:
       logger.error("Ошибка при получении детальной статистики", exc_info=e)
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = info)