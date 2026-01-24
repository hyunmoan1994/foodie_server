import base64
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from services.openai_client import analyze_food_text, analyze_food_image
from security import get_current_user

router = APIRouter()


class AnalyzeTextRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    description: str
    calories_kcal: float
    protein_g: float
    confidence: float
    notes: Optional[str] = None


# ✅ 새 표준 엔드포인트 (네가 원래 치던 형태)
@router.post("/api/analyze/text", response_model=AnalyzeResponse)
async def api_analyze_text(req: AnalyzeTextRequest):
    try:
        return await analyze_food_text(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/analyze/image", response_model=AnalyzeResponse)
async def api_analyze_image(image: UploadFile = File(...)):
    try:
        data = await image.read()
        b64 = base64.b64encode(data).decode("utf-8")
        return await analyze_food_image(b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 레거시 엔드포인트: Authorization Bearer 토큰 필요 (Railway의 기존 openapi와 호환)
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_legacy(req: AnalyzeTextRequest, user=Depends(get_current_user)):
    # user는 현재 payload dict
    try:
        return await analyze_food_text(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
