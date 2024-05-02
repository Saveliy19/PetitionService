import os

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from typing import List

from app.models import NewPetition, PetitionStatus, Like, UserInfo, PetitionsByUser, PetitionWithHeader, PetitionToGetData, PetitionData
from app.utils import add_new_petition, add_photos_to_petition, update_status_of_petition_by_id, like_petition_by_id, get_petitions_by_user_id
from app.utils import get_full_info_by_petiton_id, count_likes_by_petition_id

router = APIRouter()

# маршрут для создания новой петиции
@router.post("/make_petition")
async def make_petition(petition: NewPetition):
    try:
        petition_id = await add_new_petition(petition.is_initiative,
                                       petition.category,
                                       petition.petition_description,
                                       petition.petitioner_id,
                                       petition.latitude,
                                       petition.longtitude,
                                       petition.header)
        #if len(petition.photos) > 0:
            #await add_photos_to_petition(petition_id, petition.photos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"petition_id": f"{petition_id}"}, status.HTTP_201_CREATED

# маршрут для обновления статуса заявки
@router.post("/update_petition_status")
async def update_petition_status(petition: PetitionStatus):
    try:
        await update_status_of_petition_by_id(petition.status,
                                              petition.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return status.HTTP_200_OK

# маршрут для добавления лайка петиции
@router.post("/like_petition")
async def like_petition(like: Like):
    try:
        await like_petition_by_id(like.petition_id,
                                    like.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return status.HTTP_200_OK

# маршрут для получения списка заявок по id  пользователя
@router.post("/get_petitions")
async def get_petitions(user: UserInfo):
    try:
        result = await get_petitions_by_user_id(user.id)
        petitions = [PetitionWithHeader(id=r["id"], header=r["header"]) for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PetitionsByUser(petitions = petitions), status.HTTP_200_OK


# маршрут для получения полных данных по заявке
@router.post('/get_petition_data')
async def get_petition_data(petition: PetitionToGetData):
    try:
        info = await get_full_info_by_petiton_id(petition.id)
        likes_count = await count_likes_by_petition_id(petition.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PetitionData(id = info["id"], 
                        header = info["header"], 
                        is_initiative = info["is_initiative"], 
                        category = info["category"],
                        description = info["petition_description"],
                        status = info["petition_status"],
                        petitioner_id = info["petitioner_id"],
                        submission_time = info["submission_time"].strftime('%d.%m.%Y %H:%M'),
                        latitude = info["latitude"],
                        longitude = info["longitude"],
                        likes_count = likes_count), status.HTTP_200_OK