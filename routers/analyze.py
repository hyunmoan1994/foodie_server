import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from schemas import AnalyzeTextRequest, AnalyzeResponse, MealCreateRequest
from crud import create_meal
from services.openai_client import analyze_food_text, analyze_food_image

from security import get_current_user  # (user_id, email) 반환하도록 아래 security.py에서 맞춤

router = APIRouter(tags=["analyze"])


@router.post("/analyze/text", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeTextRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id, email = user
    result = analyze_food_text(req.text)

    # meal_date는 서버 기준 UTC를 로컬로 맞추기 귀찮으니, 앱에서 보내는 방식이 정석.
    # MVP에서는 “오늘”로 저장 (앱 캘린더 기능 붙이면 /meals로 저장하는 흐름도 가능)
    meal_date = datetime.utcnow().strftime("%Y-%m-%d")

    create_meal(
        db,
        user_id=user_id,
        email=email,
        req=MealCreateRequest(
            meal_date=meal_date,
            input_type="text",
            input_text=req.text,
            description=result["description"],
            calories_kcal=result["calories_kcal"],
            protein_g=result["protein_g"],
            confidence=result["confidence"],
            notes=result.get("notes", ""),
            warnings=result.get("warnings", []),
        ),
    )

    # UTF-8 명시 (PowerShell/콘솔 깨짐 방지에 도움)
    return JSONResponse(content=result, media_type="application/json; charset=utf-8")


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id, email = user

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    b64 = base64.b64encode(data).decode("utf-8")
    result = analyze_food_image(b64)

    meal_date = datetime.utcnow().strftime("%Y-%m-%d")

    create_meal(
        db,
        user_id=user_id,
        email=email,
        req=MealCreateRequest(
            meal_date=meal_date,
            input_type="image",
            input_text="",
            description=result["description"],
            calories_kcal=result["calories_kcal"],
            protein_g=result["protein_g"],
            confidence=result["confidence"],
            notes=result.get("notes", ""),
            warnings=result.get("warnings", []),
        ),
    )

    return JSONResponse(content=result, media_type="application/json; charset=utf-8")
