from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from app.schemas import Like

from app.managers import petition_manager

from app import logger

like_router = APIRouter()

@like_router.put("/", status_code=status.HTTP_200_OK)
async def like_petition(like: Like):
    try:
        existing_petition = petition_manager.check_existance(like.petition_id)
        if not existing_petition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await petition_manager.like_petition(like)
    except Exception as e:
        logger.error(f"Ошибка при установке лайка на заявку {like.petition_id} от {like.user_email}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@like_router.get("/{petition_id}/{user_email}", status_code=status.HTTP_200_OK)
@cache(expire=10)
async def check_like(like: Like = Depends()):
    try:
        existing_petition = petition_manager.check_existance(like.petition_id)
        if not existing_petition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        result = await petition_manager.check_user_like(like)
        return JSONResponse(content = {"result": result})
    except Exception as e:
        logger.error(f"Ошибка при проверке лайка от пользователя {like.user_email} на заявку {like.petition_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)