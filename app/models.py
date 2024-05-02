from pydantic import BaseModel
from datetime import datetime
from typing import List

class Photo(BaseModel):
    filename: str
    contents: bytes

# класс для создания новой заявки
class NewPetition(BaseModel):
    is_initiative: bool
    category: str
    petition_description: str
    petitioner_id: int
    latitude: float
    longtitude: float
    header: str
    region: str
    city_name: str
    #photos: List[Photo] = []

# класс для обновления статуса заявки
class PetitionStatus(BaseModel):
    id: int
    status: str

# класс для установки или отмены лайка
class Like(BaseModel):
    petition_id: int
    user_id: int

# класс для получения id пользователя от шлюза
class UserInfo(BaseModel):
    id: int

# класс с краткой информации о петиции
class PetitionWithHeader(BaseModel):
    id: int
    header: str

# класс, используемый для передачи массива с краткой информацией по нескольким заявкам
class PetitionsByUser(BaseModel):
    petitions: List[PetitionWithHeader]

# класс для получения данных о заявке, по которой нужно вернуть информацию
class PetitionToGetData(BaseModel):
    id: int

# класс для возврата полной информации по заявке
class PetitionData(BaseModel):
    id: int
    header: str
    is_initiative: bool
    category: str
    description: str
    status: str
    petitioner_id: int
    submission_time: str
    latitude: float
    longitude: float
    likes_count: int
    region: str
    city_name: str

class City(BaseModel):
    region: str
    name: str