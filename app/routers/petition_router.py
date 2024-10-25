import asyncio

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse

from typing import List

from app.logger import logger

from app.schemas import (NewPetition, PetitionStatus, CityWithType, City, Id,
                         PetitionWithHeader, PetitionData, Email, Petitioners, AdminPetition)

petition_router = APIRouter()

from app.managers import petition_manager

from fastapi_cache.decorator import cache

@petition_router.post("/", response_model=Id, status_code=status.HTTP_201_CREATED)
async def make_petition(petition: NewPetition):
    try:
        petition_id = await petition_manager.add_new_petition(petition)
        if petition.photos:
            await petition_manager.add_petition_photos(petition_id, petition)
        return petition_id
    except Exception as e:
        logger.error("Ошибка при создании петиции", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@petition_router.patch("/{id}/status", response_model = Petitioners, status_code=status.HTTP_200_OK)
async def update_petition_status(id: int, petition: PetitionStatus = Depends()):
    try:
        petition.id = id
        if not (await petition_manager.check_existance(petition.id)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        if not (await petition_manager.check_city_by_petition_id(petition)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='The admin does not have rights to this city')
        result, petitioner_emails = await asyncio.gather(petition_manager.update_petition_status(petition),
                                                        petition_manager.get_petitioners_email(petition))
        if result:
            return petitioner_emails
        else:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при обновлении статуса петиции", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@petition_router.get("/user/{email}", response_model=List[PetitionWithHeader], status_code=status.HTTP_200_OK)
@cache(expire=5)
async def get_petitions(email: Email = Depends()):
    try:
        petitions = await petition_manager.get_petitions_by_email(email.email)
        return petitions
    except Exception as e:
        logger.error(f"Ошибка при получении заявок пользователя {email.email}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# маршрут для получения списка заявок по названию города
@petition_router.get("/{region}/{name}", response_model=List[PetitionWithHeader], status_code=status.HTTP_200_OK)
@cache(expire=30)
async def get_city_petitions(city: CityWithType = Depends()):
    try:
        petitions = await petition_manager.get_city_petitions(city)
        return petitions
    except Exception as e:
       logger.error(f"Ошибка при получении заявок города {city.region} {city.name}", exc_info=e)
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# маршрут для получения заявок, с которыми может работать админ
@petition_router.get("/admin/{region}/{name}", response_model=List[AdminPetition], status_code=status.HTTP_200_OK)
@cache(expire=15)
async def get_admins_city_petitions(city: City = Depends()):
    try:
        petitions = await petition_manager.get_admin_petitions(city)
        return petitions
    except Exception as e:
        logger.error(f"Ошибка при получении заявок города доступных админу {city.region} {city.name}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# маршрут для получения полных данных по заявке
@petition_router.get('/{id}', response_model=PetitionData, status_code=status.HTTP_200_OK)
@cache(expire=15)
async def get_petition_data(id: int):
    try:
        existing_petition = await petition_manager.check_existance(id)
        if not existing_petition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        full_info = await petition_manager.get_full_data(id)
        return full_info
    except Exception as e:
        logger.error(f"Ошибка при получении данных заявки {id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@petition_router.get("/images/{image_path:path}")
@cache(expire=30*60)
async def get_image(image_path: str):
    try:
        return FileResponse(image_path)
    except Exception as e:
        logger.error(f"Ошибка при получении медиаданных расположенных в {image_path}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)