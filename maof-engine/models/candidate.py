"""
מודל מועמד — נועם אוקון, מעוף Tech-Lead Israel
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MilitaryRole(str, Enum):
    UNIT_COMMANDER = "unit_commander"       # מפקד כיתה ומעלה
    TECH_LEAD = "tech_lead"                 # אחראי טכני / ראש צוות
    MENTOR = "mentor"                       # חונך / מדריך
    SOLDIER = "soldier"                     # חייל ללא תפקיד ניהולי


class AcademicBackground(str, Enum):
    ATUDA = "atuda"                         # עתודאי — 100
    WARRIORS_TECH = "warriors_tech"         # לוחמים להייטק — 95
    TECH_UNIT = "tech_unit"                 # יחידה טכנולוגית — 95
    PARTIAL_DEGREE = "partial_degree"       # תואר חלקי — 85
    BAGRUT_MATH_CS = "bagrut_math_cs"       # בגרות 5 יח' מתמ' + מחשב — 80
    BAGRUT_MATH = "bagrut_math"             # בגרות 5 יח' מתמטיקה — 65
    SELF_TAUGHT = "self_taught"             # קורסים עצמאיים — 55
    REGULAR_BAGRUT = "regular_bagrut"       # בגרות רגילה — 45


class Candidate(BaseModel):
    id: str
    name: str

    # --- ציון A: כושר הוראה ---
    eli5_score: float = Field(ge=0, le=100, description="ציון ELI5 — 3 שלבים")
    subject: str = Field(description="מקצוע הוראה עיקרי")
    additional_subjects: List[str] = Field(default=[], description="מקצועות נוספים")
    distance_km: float = Field(ge=0, description="מרחק מגורים מבית הספר בק\"מ")
    family_status_score: float = Field(ge=0, le=100, description="מצב משפחתי — שאלון")
    commitment_score: float = Field(ge=0, le=100, description="מחויבות מוצהרת 1-10")
    career_switches: int = Field(ge=0, description="מספר החלפות תפקיד בצבא")
    willing_periphery: bool = Field(default=False, description="מוכן לעבור לפריפריה")

    # --- ציון B: התאמה לחברה ---
    tech_test_score: float = Field(ge=0, le=100, description="מבחן טכני — 3 חלקים")
    academic_background: AcademicBackground
    independent_courses: int = Field(ge=0, description="קורסים עצמאיים + certifications")
    promotion_rate: float = Field(ge=0, le=100, description="קצב קידום ביחס לגיל")
    military_role: MilitaryRole
    team_size: int = Field(ge=0, description="גודל הצוות שניהל")
    conflict_resolution_score: float = Field(ge=0, le=100, description="פתרון קונפליקטים")
    preferred_company_size: str = Field(description="גודל חברה מועדף")
    work_style: str = Field(description="סגנון עבודה")
    preferred_location: str = Field(description="מיקום גיאוגרפי מועדף")
    willing_relocate: bool = Field(default=False)

    # --- מטא ---
    tech_stack: List[str] = Field(default=[], description="טכנולוגיות")
    years_experience: float = Field(ge=0, default=0)
