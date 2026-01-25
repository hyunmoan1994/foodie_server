from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=1)


class AnalyzeResponse(BaseModel):
    description: str
    calories_kcal: float
    protein_g: float
    confidence: float
    notes: str = ""
    warnings: List[str] = []


class MealCreateRequest(BaseModel):
    meal_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    input_type: Literal["text", "image"] = "text"
    input_text: str = ""
    description: str = ""
    calories_kcal: float = 0.0
    protein_g: float = 0.0
    confidence: float = 0.0
    notes: str = ""
    warnings: List[str] = []


class MealOut(BaseModel):
    id: int
    user_id: str
    email: str
    meal_date: str
    input_type: str
    input_text: str
    description: str
    calories_kcal: float
    protein_g: float
    confidence: float
    notes: str
    warnings: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MealDeleteResponse(BaseModel):
    ok: bool = True
