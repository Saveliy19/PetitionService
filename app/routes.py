import os
import asyncio
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.models import (NewPetition, PetitionStatus, Like, UserInfo, PetitionsByUser, PetitionWithHeader, 
                        PetitionToGetData, PetitionData, CityWithType, SubjectForBriefAnalysis, City, 
                        AdminPetition, AdminPetitions, Comment, RegionForDetailedAnalysis)
from app.utils import (add_new_petition, add_photos_to_petition, update_status_of_petition_by_id, 
                       like_petition_by_id, get_petitions_by_user_email, get_full_info_by_petiton_id, 
                       get_comments_by_petition_id, get_petitions_by_city, get_brief_subject_analysis, 
                       check_user_like, get_admin_petitions, get_photos_by_petition_id, 
                       get_petitioner_emails_by_petition_id, get_full_statistics, check_city_by_petition_id)

router = APIRouter()

# маршрут для создания новой петиции
@router.post("/make_petition")
async def make_petition(petition: NewPetition):
    try:
        petition_id = await add_new_petition(petition.is_initiative,
                                       petition.category,
                                       petition.petition_description,
                                       petition.petitioner_email,
                                       petition.address,
                                       petition.header,
                                       petition.region,
                                       petition.city_name)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if len(petition.photos) > 0:
            await add_photos_to_petition(petition_id, petition.photos)
    return {"petition_id": f"{petition_id}"}, status.HTTP_201_CREATED

# маршрут для обновления статуса заявки
@router.put("/update_petition_status")
async def update_petition_status(petition: PetitionStatus):
    if not (await check_city_by_petition_id(petition.id, petition.admin_region, petition.admin_city)):
        raise HTTPException(status_code=403, detail='The admin does not have rights to this city')
    try:
        result, petitioner_emails = await asyncio.gather(update_status_of_petition_by_id(petition.status,
                                                petition.id,
                                                petition.admin_id,
                                                petition.comment),
                                                get_petitioner_emails_by_petition_id(petition.id))
    except:
        raise HTTPException(status_code=500)
    if result:
        return {"petitioner_emails": petitioner_emails}, status.HTTP_200_OK
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR

# маршрут для проверки лайка
@router.post("/check_like")
async def check_like(content: Like):
    try:
        result = await check_user_like(content.petition_id,
                                       content.user_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"result": result}

# маршрут для добавления лайка петиции
@router.put("/like_petition")
async def like_petition(like: Like):
    try:
        await like_petition_by_id(like.petition_id,
                                    like.user_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return status.HTTP_200_OK

# маршрут для получения списка заявок по id  пользователя
@router.post("/get_petitions")
async def get_petitions(user: UserInfo):
    try:
        result = await get_petitions_by_user_email(user.email)
        petitions = [PetitionWithHeader(id=r["id"], 
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes = r["likes_count"]) for r in result]
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
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
        petitions = [AdminPetition(id=r["id"],
                                        header=r["header"], 
                                        status=r["petition_status"], 
                                        address=r["address"], 
                                        date=r["submission_time"].strftime('%d.%m.%Y %H:%M'),
                                        likes=r["likes_count"],
                                        type = 'Жалоба' if r["is_initiative"] == False else 'Инициатива') for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return AdminPetitions(petitions = petitions), status.HTTP_200_OK

# маршрут для получения полных данных по заявке
@router.post('/get_petition_data')
async def get_petition_data(petition: PetitionToGetData):
    try:
        info, comments, photos = await asyncio.gather(get_full_info_by_petiton_id(petition.id),
                                                      get_comments_by_petition_id(petition.id),
                                                      get_photos_by_petition_id(petition.id))
        output_comments = [Comment(date=c["submission_time"].strftime('%d.%m.%Y %H:%M'), data=c["comment_description"]) for c in comments]
        print(photos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PetitionData(id = info["id"], 
                        header = info["header"], 
                        is_initiative = info["is_initiative"], 
                        category = info["category"],
                        description = info["petition_description"],
                        status = info["petition_status"],
                        petitioner_email = info["petitioner_email"],
                        submission_time = info["submission_time"].strftime('%d.%m.%Y %H:%M'),
                        address = info["address"],
                        region = info["region"],
                        city_name = info["city_name"],
                        likes_count = info["likes_count"],
                        comments = output_comments,
                        photos = photos), status.HTTP_200_OK

@router.get("/images/{image_path:path}")
async def get_image(image_path: str):
    return FileResponse(image_path)


# маршрут для получения краткой аналитики по населенному пункту
@router.post("/get_brief_analysis")
async def get_brief_analysis(subject: SubjectForBriefAnalysis):
    try:
        Info = await get_brief_subject_analysis(subject.region, subject.name, subject.period)
    except:
        raise HTTPException(status_code=500)
    return Info, status.HTTP_200_OK

#  маршрут для получения подробного анализа
@router.post("/get_detailed_analysis")
async def get_brief_analysis(subject: RegionForDetailedAnalysis):
    try:
        Info = await get_full_statistics(subject.region_name, 
                                            subject.city_name, 
                                            subject.start_time, 
                                            subject.end_time, 
                                            subject.rows_count)
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
    return Info, status.HTTP_200_OK