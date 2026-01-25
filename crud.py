import json
from sqlalchemy.orm import Session
from models import MealLog
from schemas import MealCreateRequest


def create_meal(db: Session, user_id: str, email: str, req: MealCreateRequest) -> MealLog:
    warnings_json = json.dumps(req.warnings, ensure_ascii=False)
    row = MealLog(
        user_id=user_id,
        email=email or "",
        meal_date=req.meal_date,
        input_type=req.input_type,
        input_text=req.input_text or "",
        description=req.description or "",
        calories_kcal=req.calories_kcal or 0.0,
        protein_g=req.protein_g or 0.0,
        confidence=req.confidence or 0.0,
        notes=req.notes or "",
        warnings=warnings_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_meals_by_date(db: Session, user_id: str, meal_date: str) -> list[MealLog]:
    return (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.meal_date == meal_date)
        .order_by(MealLog.created_at.desc())
        .all()
    )


def list_meals_range(db: Session, user_id: str, start_date: str, end_date: str) -> list[MealLog]:
    # 문자열 비교가 YYYY-MM-DD에서 정렬/범위 비교 동작
    return (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.meal_date >= start_date, MealLog.meal_date <= end_date)
        .order_by(MealLog.meal_date.asc(), MealLog.created_at.desc())
        .all()
    )


def delete_meal(db: Session, user_id: str, meal_id: int) -> bool:
    row = db.query(MealLog).filter(MealLog.user_id == user_id, MealLog.id == meal_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
