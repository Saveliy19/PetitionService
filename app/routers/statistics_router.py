from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import SubjectForBriefAnalysis, RegionForDetailedAnalysis, FullStatistics, BriefAnalysis
from app.managers import statistics_manager

from app.logger import logger

from fastapi_cache.decorator import cache

statistics_router = APIRouter()


# маршрут для получения краткой аналитики по населенному пункту
@statistics_router.get("/brief/{region_name}/{city_name}", response_model=BriefAnalysis, status_code=status.HTTP_200_OK)
@cache(expire=60*60)
async def get_brief_analysis(subject: SubjectForBriefAnalysis = Depends()):
    try:
        info = await statistics_manager.get_brief_subject_analysis(subject)
        return info
    except Exception as e:
        logger.error("Ошибка при получении краткой статистики", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@statistics_router.get("/detailed/{region_name}/{city_name}", response_model=FullStatistics, status_code=status.HTTP_200_OK)
# @cache(expire=240)
async def get_detailed_analysis(subject: RegionForDetailedAnalysis = Depends()):
    try:
        info = await statistics_manager.get_full_statistics(subject)
        return info
    except Exception as e:
        logger.error("Ошибка при получении детальной статистики", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
