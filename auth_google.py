import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from jose import jwt
from datetime import datetime, timedelta
import uuid

from main import USERS, create_access_token

router = APIRouter(prefix="/auth/google", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_REDIRECT_URI = os.getenv("FRONTEND_REDIRECT_URI")


@router.get("/login")
def google_login():
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url)


@router.get("/callback")
def google_callback(code: str):
    # 1. Access token 요청
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    ).json()

    if "access_token" not in token_res:
        raise HTTPException(status_code=400, detail="Google token error")

    # 2. 사용자 정보 조회
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token_res['access_token']}"},
    ).json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email")

    # 3. 유저 조회 or 생성
    for u in USERS.values():
        if u["provider"] == "google" and u["provider_user_id"] == email:
            token = create_access_token(u["id"])
            return RedirectResponse(f"{FRONTEND_REDIRECT_URI}?token={token}")

    user_id = str(uuid.uuid4())
    USERS[user_id] = {
        "id": user_id,
        "provider": "google",
        "provider_user_id": email,
        "created_at": datetime.utcnow().isoformat(),
    }

    token = create_access_token(user_id)
    return RedirectResponse(f"{FRONTEND_REDIRECT_URI}?token={token}")
