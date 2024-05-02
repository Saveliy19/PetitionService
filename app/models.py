from pydantic import BaseModel
from typing import List

class Photo(BaseModel):
    filename: str
    contents: bytes

class NewPetition(BaseModel):
    is_initiative: bool
    category: str
    petition_description: str
    petitioner_id: int
    latitude: float
    longtitude: float
    header: str
    #photos: List[Photo] = []