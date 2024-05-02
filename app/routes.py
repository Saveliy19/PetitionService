import os

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from typing import List

from app.models import NewPetition
from app.utils import add_new_petition, add_photos_to_petition

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