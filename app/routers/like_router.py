from fastapi import Depends, APIRouter, HTTPException, status
from fastapi_cache.decorator import cache

from app.schemas import Like
from app.managers import petition_manager
from app.schemas import IsLiked

from app import logger

like_router = APIRouter()

@like_router.put("/{petition_id}", response_model=IsLiked, status_code=status.HTTP_200_OK)
async def like_petition(petition_id: int, like: Like):
    try:
        like.petition_id = petition_id
        if not await petition_manager.check_existance(like.petition_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return await petition_manager.like_petition(like)
    except Exception as e:
        logger.error(f"Ошибка при установке лайка на заявку {like.petition_id} от {like.user_email}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@like_router.get("/{petition_id}/{user_email}", response_model=IsLiked, status_code=status.HTTP_200_OK)
#@cache(expire=10)
async def check_like(like: Like = Depends()):
    try:
        if not await petition_manager.check_existance(like.petition_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        result = await petition_manager.check_user_like(like)
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке лайка от пользователя {like.user_email} на заявку {like.petition_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)