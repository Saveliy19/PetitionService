from pydantic import BaseModel, EmailStr
from typing import Dict, List

class Petition(BaseModel):
    id: int
    header: str
    category: str
    date: str
    like_count: int

class FullStatistics(BaseModel):
    complaints_count_per_category_city: Dict
    initiatives_count_per_category_city: Dict
    avg_complaints_count_per_category_region: Dict
    avg_initiatives_count_per_category_region: Dict
    city_initiatives_count_per_day: Dict
    city_complaints_count_per_day: Dict
    most_popular_city_complaints: List[Petition]
    most_popular_city_initiatives: List[Petition]


class BriefAnalysis(BaseModel):
    most_popular_city_complaints: List[Petition]
    most_popular_city_initiatives: List[Petition]
    most_popular_region_complaints: List[Petition]
    most_popular_region_initiatives: List[Petition]
    city_complaints_count_per_status: Dict
    city_initiatives_count_per_status: Dict
    region_complaints_count_per_status: Dict
    region_initiatives_count_per_status: Dict

class IsLiked(BaseModel):
    is_liked: bool

class Emails(BaseModel):
    emails: List[EmailStr]


class Petitioners(BaseModel):
    petitioners_emails: List[EmailStr]

class Comment(BaseModel):
    date: str
    data: str

class PetitionData(BaseModel):
    id: int
    header: str
    is_initiative: bool
    category: str
    description: str
    status: str
    petitioner_email: str
    submission_time: str
    address: str
    likes_count: int
    region: str
    city_name: str
    comments: List[Comment]
    photos: List[str]


# класс с краткой информации о петиции
class PetitionWithHeader(BaseModel):
    id: int
    header: str
    status: str
    address: str
    date: str
    likes: int

class AdminPetition(PetitionWithHeader):
    type: str