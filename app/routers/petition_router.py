import asyncio

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse

from typing import List

from app import logger

from app.schemas import NewPetition, PetitionStatus, CityWithType, City, PetitionToGetData, PetitionWithHeader

petition_router = APIRouter()

from app.managers import petition_manager

from fastapi_cache.decorator import cache

@petition_router.post("/", status_code=status.HTTP_201_CREATED)
async def make_petition(petition: NewPetition):
    try:
        petition_id = await petition_manager.add_new_petition(petition)
        if petition.photos:
            await petition_manager.add_petition_photos(petition_id, petition.photos)
            return JSONResponse(content = petition_id)
    except Exception as e:
        logger.error("Ошибка при создании петиции", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@petition_router.patch("/petition/status", status_code=status.HTTP_200_OK)
async def update_petition_status(petition: PetitionStatus):
    try:
        existing_petition = petition_manager.check_existance(petition.id)
        if not existing_petition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        if not (await petition_manager.check_city_by_petition_id(petition)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='The admin does not have rights to this city')
        result, petitioner_emails = await asyncio.gather(petition_manager.update_petition_status(petition),
                                                        petition_manager.get_petitioners_email(petition))
        if result:
            return JSONResponse(content = petitioner_emails)
        else:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Ошибка при обновлении статуса петиции", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@cache(expire=60)
@petition_router.get("/{user_email}", status_code=status.HTTP_200_OK)
async def get_petitions(user_email: str):
    try:
        petitions = await petition_manager.get_petitions_by_email(user_email)
        return JSONResponse(content={"petitions": petitions})
    except Exception as e:
        logger.error(f"Ошибка при получении заявок пользователя {user_email}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# маршрут для получения списка заявок по названию города
@petition_router.get("/{region}/{name}", response_model=List[PetitionWithHeader], status_code=status.HTTP_200_OK)
@cache(expire=60)
async def get_city_petitions(city: CityWithType = Depends()):
    try:
        petitions = await petition_manager.get_city_petitions(city)
        return petitions
    except Exception as e:
       logger.error(f"Ошибка при получении заявок города {city.region} {city.name}", exc_info=e)
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# маршрут для получения заявок, с которыми может работать админ
@petition_router.get("/admin/{region}/{name}", status_code=status.HTTP_200_OK)
@cache(expire=60)
async def get_admins_city_petitions(city: City = Depends()):
    try:
        petitions = await petition_manager.get_admin_petitions(city)
        return JSONResponse(content = {"petitions": petitions})
    except Exception as e:
        logger.error(f"Ошибка при получении заявок города доступных админу {city.region} {city.name}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# маршрут для получения полных данных по заявке
@petition_router.get('/{id}', status_code=status.HTTP_200_OK)
@cache(expire=60)
async def get_petition_data(petition: PetitionToGetData = Depends()):
    try:
        existing_petition = petition_manager.check_existance(petition.id)
        if not existing_petition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        full_info = petition_manager.get_full_data(petition)
        return JSONResponse(content = full_info)
    except Exception as e:
        logger.error(f"Ошибка при получении данных заявки {petition.id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@petition_router.get("/images/{image_path:path}")
@cache(expire=30*60)
async def get_image(image_path: str):
    try:
        return FileResponse(image_path)
    except Exception as e:
        logger.error(f"Ошибка при получении медиаданных расположенных в {image_path}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)