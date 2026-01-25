import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from db import get_db
from security import get_current_user
from schemas import MealCreateRequest, MealOut, MealDeleteResponse
from crud import create_meal, list_meals_by_date, list_meals_range, delete_meal

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("", response_model=MealOut)
def add_meal(req: MealCreateRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id, email = user
    row = create_meal(db, user_id=user_id, email=email, req=req)

    # warnings는 DB에 JSON string이라 변환해서 내려줌
    warnings = []
    try:
        warnings = json.loads(row.warnings or "[]")
    except Exception:
        warnings = []

    return MealOut(
        id=row.id,
        user_id=row.user_id,
        email=row.email,
        meal_date=row.meal_date,
        input_type=row.input_type,
        input_text=row.input_text,
        description=row.description,
        calories_kcal=row.calories_kcal,
        protein_g=row.protein_g,
        confidence=row.confidence,
        notes=row.notes,
        warnings=warnings,
        created_at=row.created_at,
    )


@router.get("", response_model=list[MealOut])
def get_meals(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    start: str | None = Query(default=None, description="YYYY-MM-DD"),
    end: str | None = Query(default=None, description="YYYY-MM-DD"),
):
    user_id, _ = user

    if date:
        rows = list_meals_by_date(db, user_id=user_id, meal_date=date)
    else:
        if not (start and end):
            raise HTTPException(status_code=400, detail="Provide either date or (start,end)")
        rows = list_meals_range(db, user_id=user_id, start_date=start, end_date=end)

    out = []
    for r in rows:
        try:
            warnings = json.loads(r.warnings or "[]")
        except Exception:
            warnings = []
        out.append(
            MealOut(
                id=r.id,
                user_id=r.user_id,
                email=r.email,
                meal_date=r.meal_date,
                input_type=r.input_type,
                input_text=r.input_text,
                description=r.description,
                calories_kcal=r.calories_kcal,
                protein_g=r.protein_g,
                confidence=r.confidence,
                notes=r.notes,
                warnings=warnings,
                created_at=r.created_at,
            )
        )
    return out


@router.delete("/{meal_id}", response_model=MealDeleteResponse)
def remove_meal(meal_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id, _ = user
    ok = delete_meal(db, user_id=user_id, meal_id=meal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return MealDeleteResponse(ok=True)
