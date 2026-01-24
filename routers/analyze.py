# routers/analyze.py
import base64
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.openai_client import analyze_food_text, analyze_food_image

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeTextRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    description: str
    calories_kcal: float
    protein_g: float
    confidence: float
    notes: Optional[str] = None


@router.post("/analyze/text", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeTextRequest):
    try:
        result = analyze_food_text(req.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(image: UploadFile = File(...)):
    try:
        data = await image.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty image file")

        b64 = base64.b64encode(data).decode("utf-8")
        result = analyze_food_image(b64)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
