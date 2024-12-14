from app.schemas import Like, IsLiked


class LikeManager:
    def __init__(self, db):
        self.db = db

    async def delete_like(self, like: Like):
        query = '''DELETE FROM LIKES WHERE PETITION_ID = $1 AND USER_EMAIL = $2;'''
        await self.db.exec_query(query, like.petition_id, like.user_email)
        return IsLiked(is_liked=False)

    async def like_petition(self, like: Like):
        query = '''INSERT INTO LIKES (PETITION_ID, USER_EMAIL) VALUES ($1, $2);'''
        await self.db.exec_query(query, like.petition_id, like.user_email)
        return IsLiked(is_liked=True)

    # проверяем лайк пользователя на записи
    async def check_user_like(self, like: Like):
        query = '''SELECT * FROM LIKES WHERE PETITION_ID = $1 AND USER_EMAIL = $2;'''
        result = True
        existing_like = await self.db.select_one(query, like.petition_id, like.user_email)
        if not existing_like:
            result = False
        return IsLiked(is_liked=result)
