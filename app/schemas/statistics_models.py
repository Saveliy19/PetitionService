from pydantic import BaseModel
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