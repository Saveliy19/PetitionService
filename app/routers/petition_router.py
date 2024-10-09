import asyncio

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse

from app.models import NewPetition, PetitionStatus, CityWithType, City, PetitionToGetData, Like, PetitionData

petition_router = APIRouter()
from app.dependencies import petition_manager

@petition_router.post("/petition", status_code=status.HTTP_201_CREATED)
async def make_petition(petition: NewPetition):
    try:
        petition_id = await petition_manager.add_new_petition(petition)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if petition.photos:
            await petition_manager.add_petition_photos(petition_id, petition.photos)
    return JSONResponse(content = petition_id)

@petition_router.patch("/petition/status", status_code=status.HTTP_200_OK)
async def update_petition_status(petition: PetitionStatus):
    if not (await petition_manager.check_city_by_petition_id(petition)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='The admin does not have rights to this city')
    try:
        result, petitioner_emails = await asyncio.gather(petition_manager.update_petition_status(petition),
                                                        petition_manager.get_petitioners_email(petition))
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if result:
        return JSONResponse(content = petitioner_emails)
    else:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    
@petition_router.get("/{user_email}", status_code=status.HTTP_200_OK)
async def get_petitions(user_email: str):
    try:
        petitions = await petition_manager.get_petitions_by_email(user_email)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return JSONResponse(content={"petitions": petitions})

# маршрут для получения списка заявок по названию города
@petition_router.get("/{region}/{name}", status_code=status.HTTP_200_OK)
async def get_city_petitions(city: CityWithType = Depends()):
    try:
        petitions = await petition_manager.get_city_petitions(city)
    except Exception as e:
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = {"petitions": petitions})

# маршрут для получения заявок, с которыми может работать админ
@petition_router.get("/admin/{region}/{name}", status_code=status.HTTP_200_OK)
async def get_admins_city_petitions(city: City = Depends()):
    try:
        petitions = await petition_manager.get_admin_petitions(city)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = {"petitions": petitions})

# маршрут для получения полных данных по заявке
@petition_router.get('/petition{id}', status_code=status.HTTP_200_OK)
async def get_petition_data(petition: PetitionToGetData = Depends()):
    try:
        info, output_comments, photos = await asyncio.gather(petition_manager.get_full_petition_info(petition.id),
                                                      petition_manager.get_petition_comments(petition.id),
                                                      petition_manager.get_petition_photos(petition.id))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                        photos = photos)


@petition_router.get("/{petition_id}/like/{user_email}", status_code=status.HTTP_200_OK)
async def check_like(like: Like = Depends()):
    try:
        result = await petition_manager.check_user_like(like)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content = {"result": result})

@petition_router.put("/like", status_code=status.HTTP_200_OK)
async def like_petition(like: Like):
    try:
        result = await petition_manager.like_petition(like)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition doesn't exists!")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@petition_router.get("/images/{image_path:path}")
async def get_image(image_path: str):
    return FileResponse(image_path)