from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from security import get_current_user
from services.openai_client import analyze_food_text, analyze_food_image

router = APIRouter(tags=["analyze"])


class AnalyzeTextRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    description: str
    calories_kcal: float
    protein_g: float
    confidence: float
    notes: str | None = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeTextRequest, user=Depends(get_current_user)):
    try:
        return analyze_food_text(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(image: UploadFile = File(...), user=Depends(get_current_user)):
    try:
        data = await image.read()
        return analyze_food_image(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- 호환용 alias (필요하면 앱/스크립트가 이쪽을 칠 수도 있음)
@router.post("/analyze/text", response_model=AnalyzeResponse)
async def analyze_text_alias(req: AnalyzeTextRequest, user=Depends(get_current_user)):
    return await analyze_text(req, user)
