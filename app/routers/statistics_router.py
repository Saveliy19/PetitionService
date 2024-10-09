from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse

from app.models import SubjectForBriefAnalysis, RegionForDetailedAnalysis
from app.dependencies import statistics_manager

statistics_router = APIRouter()

# маршрут для получения краткой аналитики по населенному пункту
@statistics_router.get("/brief/{region_name}/{city_name}", status_code=status.HTTP_200_OK)
async def get_brief_analysis(subject: SubjectForBriefAnalysis = Depends()):
    try:
        info = await statistics_manager.get_brief_subject_analysis(subject.region, subject.name, subject.period)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = info)


@statistics_router.get("/detailed/{region_name}/{city_name}", status_code=status.HTTP_200_OK)
async def get_detailed_analysis(subject: RegionForDetailedAnalysis = Depends()):
    try:
        info = await statistics_manager.get_full_statistics(subject.region_name, 
                                                            subject.city_name, 
                                                            subject.start_time, 
                                                            subject.end_time, 
                                                            subject.rows_count)
    except Exception as e:
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = info)