import os
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import jwt, JWTError
from openai import OpenAI
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Base, User, History

# ======================
# ENV / CONFIG
# ======================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = "HS256"

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================
# DB INIT
# ======================
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================
# APP
# ======================
app = FastAPI(title="Foodie Server")

# ======================
# Schemas
# ======================
class DevLoginRequest(BaseModel):
    provider: str
    provider_user_id: str

class AnalyzeRequest(BaseModel):
    text: str

class UpdateHistoryRequest(BaseModel):
    message: str

# ======================
# JWT
# ======================
def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# ======================
# Health
# ======================
@app.get("/health")
def health():
    return {"status": "ok"}

# ======================
# Auth (DEV)
# ======================
@app.post("/auth/dev-login")
def dev_login(req: DevLoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.provider == req.provider,
            User.provider_user_id == req.provider_user_id,
        )
        .first()
    )

    if not user:
        user = User(
            provider=req.provider,
            provider_user_id=req.provider_user_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)
    return {"access_token": token}

# ======================
# Analyze
# ======================
@app.post("/analyze")
def analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = f"""
    사용자가 먹은 음식: {req.text}

    1. 예상 칼로리 범위
    2. 소모를 위한 권장 걷기 운동 시간 (분)
    3. 간단한 설명
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    history = History(
        user_id=user.id,
        message=message,
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "message": history.message,
        "created_at": history.created_at.isoformat(),
    }

# ======================
# History
# ======================
@app.get("/users/me/history")
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(History)
        .filter(History.user_id == user.id)
        .order_by(History.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "history": [
            {
                "id": h.id,
                "message": h.message,
                "created_at": h.created_at.isoformat(),
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            }
            for h in items
        ]
    }

@app.put("/users/me/history/{history_id}")
def update_history(
    history_id: str,
    req: UpdateHistoryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(History)
        .filter(
            History.id == history_id,
            History.user_id == user.id,
        )
        .first()
    )

    if not history:
        raise HTTPException(status_code=404, detail="Not found")

    history.message = req.message
    history.updated_at = datetime.utcnow()
    db.commit()

    return {"ok": True}
