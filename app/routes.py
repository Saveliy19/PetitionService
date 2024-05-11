import os

import asyncio

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from typing import List

from app.models import NewPetition, PetitionStatus, Like, UserInfo, PetitionsByUser, PetitionWithHeader, PetitionToGetData, PetitionData, CityWithType
from app.models import SubjectForBriefAnalysis, PetitionIdWithUserId, City
from app.utils import add_new_petition, add_photos_to_petition, update_status_of_petition_by_id, like_petition_by_id, get_petitions_by_user_id
from app.utils import get_full_info_by_petiton_id, count_likes_by_petition_id, get_petitions_by_city, get_brief_subject_analysis, check_user_like
from app.utils import get_admin_petitions

router = APIRouter()

# маршрут для создания новой петиции
@router.post("/make_petition")
async def make_petition(petition: NewPetition):
    try:
        petition_id = await add_new_petition(petition.is_initiative,
                                       petition.category,
                                       petition.petition_description,
                                       petition.petitioner_id,
                                       petition.address,
                                       petition.header,
                                       petition.region,
                                       petition.city_name)
        #if len(petition.photos) > 0:
            #await add_photos_to_petition(petition_id, petition.photos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"petition_id": f"{petition_id}"}, status.HTTP_201_CREATED

# маршрут для обновления статуса заявки
@router.post("/update_petition_status")
async def update_petition_status(petition: PetitionStatus):
    try:
        result = await update_status_of_petition_by_id(petition.status,
                                              petition.id,
                                              petition.admin_id,
                                              petition.comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if result:
        return status.HTTP_200_OK
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR

# маршрут для проверки лайка
@router.post("/check_like")
async def check_like(content: Like):
    try:
        result = await check_user_like(content.petition_id,
                                       content.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"result": result}

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
    #try:
    result = await get_petitions_by_user_id(user.id)
    petitions = [PetitionWithHeader(id=r["id"], 
                                    header=r["header"], 
                                    status=r["petition_status"], 
                                    address=r["address"], 
                                    date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                    likes = r["likes_count"]) for r in result]
    #except Exception as e:
       #raise HTTPException(status_code=500, detail=str(e))
    return PetitionsByUser(petitions = petitions), status.HTTP_200_OK

# маршрут для получения списка заявок по названию города
@router.post("/get_city_petitions")
async def get_city_petitions(city: CityWithType):
    try:
        result = await get_petitions_by_city(city.region, city.name, city.is_initiative)
        petitions = [PetitionWithHeader(id=r["id"], 
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes=r["likes_count"]) for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PetitionsByUser(petitions = petitions), status.HTTP_200_OK

# маршрут для получения заявок, с которыми может работать админ
@router.post("/get_admins_city_petitions")
async def get_admins_city_petitions(city: City):
    try:
        result = await get_admin_petitions(city.region, city.name)
        petitions = [PetitionWithHeader(id=r["id"], 
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes=r["likes_count"]) for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PetitionsByUser(petitions = petitions), status.HTTP_200_OK

# маршрут для получения полных данных по заявке
@router.post('/get_petition_data')
async def get_petition_data(petition: PetitionToGetData):
    try:
        info, likes_count = await asyncio.gather(get_full_info_by_petiton_id(petition.id), count_likes_by_petition_id(petition.id))
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
                        address = info["address"],
                        region = info["region"],
                        city_name = info["city_name"],
                        likes_count = likes_count), status.HTTP_200_OK


# маршрут для получения краткой аналитики по населенному пункту
@router.post("/get_brief_analysis")
async def get_brief_analysis(subject: SubjectForBriefAnalysis):
    try:
        Info = await get_brief_subject_analysis(subject.type, subject.name, subject.period)
        print(Info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Info, status.HTTP_200_OK
