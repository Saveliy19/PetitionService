import os
import base64

from app.schemas import NewPetition


class MediaManager:
    def __init__(self, db, main_folder_path):
        self.db = db
        self.main_folder_path = main_folder_path

    # добавляем фотографии петиции
    async def add_petition_photos(self, petition_id: int, petition: NewPetition):
        folder_path = self.main_folder_path + f"{petition_id}"
        os.mkdir(folder_path)
        for p in petition.photos:
            with open(self.main_folder_path + f'{petition_id}/{p.filename}', 'wb') as f:
                f.write(base64.b64decode(p.content))

        query = '''INSERT INTO PHOTO_FOLDER (PETITION_ID, FOLDER_PATH) VALUES ($1, $2);'''
        await self.db.exec_query(query, petition_id, folder_path)

    # получаем фотографии петиции
    async def get_petition_photos(self, petition_id):
        photos = []
        query = '''SELECT FOLDER_PATH FROM PHOTO_FOLDER WHERE PETITION_ID = $1;'''
        try:
            folder_path = (await self.db.select_one(query, petition_id))["folder_path"]
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                photos.append('http://127.0.0.1:8002/images/' + file_path)
        except TypeError:
            pass
        return photos
