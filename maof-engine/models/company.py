"""
מודל חברת הייטק — מעוף Tech-Lead Israel
"""

from pydantic import BaseModel, Field
from typing import List


class Company(BaseModel):
    id: str
    name: str
    location: str
    lat: float
    lng: float

    # פרופיל
    size: str = Field(description="גודל חברה — startup/mid/enterprise")
    work_style: str = Field(description="סגנון עבודה — agile/waterfall/hybrid")
    tech_stack: List[str] = Field(description="טכנולוגיות נדרשות")

    # דחיפות
    open_positions: int = Field(ge=0, description="משרות פתוחות")
    urgency_score: float = Field(ge=0, le=100, description="דחיפות גיוס")

    # תחנה ב'
    willing_station_b: bool = Field(default=True, description="מוכן לתחנה ב'")
    placement_fee_paid: bool = Field(default=False, description="עמלת 35K שולמה")
