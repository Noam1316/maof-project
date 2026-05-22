"""
מודל בית ספר — מעוף Tech-Lead Israel
"""

from pydantic import BaseModel, Field
from typing import List


class School(BaseModel):
    id: str
    name: str
    location: str
    lat: float
    lng: float

    # צרכי הוראה
    required_subjects: List[str] = Field(description="מקצועות נדרשים")
    grade_levels: List[str] = Field(description="רמות כיתה — ז'-י\"ב")

    # מדדי השפעה
    socioeconomic_rank: int = Field(ge=1, le=10, description="דירוג סוציו-אקונומי — למ\"ס")
    nurturing_index: int = Field(ge=1, le=10, description="מדד טיפוח — משרד החינוך")
    months_without_teacher: int = Field(ge=0, description="חודשים ללא מורה במקצוע")

    # תקציב
    budget_available: bool = Field(default=True, description="תקציב גפ\"ן זמין")
