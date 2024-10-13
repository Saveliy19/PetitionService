from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class Photo(BaseModel):
    filename: str
    content: str

# класс для создания новой заявки
class NewPetition(BaseModel):
    is_initiative: bool
    category: str
    petition_description: str
    petitioner_email: str
    address: str
    header: str
    region: str
    city_name: str
    photos: Optional[List[Photo]] = None

# класс для обновления статуса заявки
class PetitionStatus(BaseModel):
    id: int = None
    admin_id: int
    admin_city: str
    admin_region: str
    status: str
    comment: str

class Like(BaseModel):
    petition_id: int = None
    user_email: str

class City(BaseModel):
    region: str
    name: str
    limit: int
    offset: int

class CityWithType(City):
    is_initiative: bool

class SubjectForBriefAnalysis(City):
    start_time: datetime
    end_time: datetime

class RegionForDetailedAnalysis(BaseModel):
    region_name: str
    city_name: str
    start_time: datetime
    end_time: datetime
    rows_count: int

class Email(BaseModel):
    email: EmailStr

