import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ======================
# ENV
# ======================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

JWT_SECRET = os.getenv("SECRET_KEY", "dev-secret")
JWT_ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_REDIRECT_URI = os.getenv("FRONTEND_REDIRECT_URI")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Foodie Server")

# ======================
# In-memory DB (v1)
# ======================
USERS = {}      # user_id -> user
HISTORY = {}    # user_id -> history list

# ======================
# Models
# ======================
class AnalyzeRequest(BaseModel):
    text: str


# ======================
# JWT
# ======================
def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = USERS.get(user_id)
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
# Google OAuth
# ======================
@app.get("/auth/google/login")
def google_login():
    if not all([GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Google OAuth env missing")

    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(url)


@app.get("/auth/google/callback")
async def google_callback(code: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    async with httpx.AsyncClient() as http:
        token_res = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    async with httpx.AsyncClient() as http:
        userinfo_res = await http.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    profile = userinfo_res.json()
    google_id = profile["id"]
    email = profile.get("email")

    # 유저 조회 / 생성
    user = None
    for u in USERS.values():
        if u["provider"] == "google" and u["provider_user_id"] == google_id:
            user = u
            break

    if not user:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "provider": "google",
            "provider_user_id": google_id,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
        }
        USERS[user_id] = user
        HISTORY[user_id] = []

    jwt_token = create_access_token(user["id"])

    redirect_url = f"{FRONTEND_REDIRECT_URI}?token={jwt_token}"
    return RedirectResponse(redirect_url)


# ======================
# Analyze
# ======================
@app.post("/analyze")
def analyze(req: AnalyzeRequest, user=Depends(get_current_user)):
    prompt = f"""
    사용자가 먹은 음식: {req.text}

    1. 예상 칼로리 범위
    2. 단백질 함량 추정
    3. 간단한 설명
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    message = response.choices[0].message.content

    result = {
        "id": str(uuid.uuid4()),
        "text": req.text,
        "message": message,
        "created_at": datetime.utcnow().isoformat(),
    }

    HISTORY[user["id"]].insert(0, result)
    HISTORY[user["id"]] = HISTORY[user["id"]][:30]

    return result


# ======================
# History
# ======================
@app.get("/users/me/history")
def get_history(user=Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "history": HISTORY.get(user["id"], []),
    }
