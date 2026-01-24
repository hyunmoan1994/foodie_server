import os
import time
from typing import Optional

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# 최종 리다이렉트(프론트가 아직 없으니 서버가 token 보여주는 페이지로 둠)
FRONTEND_REDIRECT_URI = os.getenv(
    "FRONTEND_REDIRECT_URI",
    "https://foodieserver-production.up.railway.app/auth/finish",
)

def _require_env(name: str, value: Optional[str]):
    if not value:
        raise RuntimeError(f"Missing env var: {name}")

@router.get("/auth/google/login")
def google_login():
    _require_env("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID)
    _require_env("GOOGLE_REDIRECT_URI", GOOGLE_REDIRECT_URI)

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(url=google_auth_url, status_code=307)

@router.get("/auth/google/callback")
async def google_callback(request: Request, code: Optional[str] = None):
    _require_env("SECRET_KEY", SECRET_KEY)
    _require_env("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID)
    _require_env("GOOGLE_CLIENT_SECRET", GOOGLE_CLIENT_SECRET)
    _require_env("GOOGLE_REDIRECT_URI", GOOGLE_REDIRECT_URI)

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # 1) code -> access_token
    async with httpx.AsyncClient(timeout=15.0) as http:
        token_res = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"token exchange failed: {token_res.text}")

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    # 2) access_token -> userinfo
    async with httpx.AsyncClient(timeout=15.0) as http:
        user_res = await http.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"userinfo failed: {user_res.text}")

    user_info = user_res.json()
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Failed to get user info (no email)")

    # 3) JWT 발급
    payload = {
        "sub": email,
        "email": email,
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # 4) finish 페이지로 리다이렉트
    # FRONTEND_REDIRECT_URI가 이미 /auth/finish면 그대로 쓴다.
    redirect_url = f"{FRONTEND_REDIRECT_URI}?token={jwt_token}"
    return RedirectResponse(url=redirect_url, status_code=307)

@router.get("/auth/finish", response_class=HTMLResponse)
def auth_finish(token: Optional[str] = None):
    # 프론트가 없을 때 token을 눈으로 확인하는 임시 페이지
    if not token:
        return HTMLResponse(
            "<h3>Auth finished</h3><p>No token provided.</p>",
            status_code=200,
        )

    html = f"""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Auth Finish</title></head>
  <body style="font-family: Arial, sans-serif; padding: 24px;">
    <h3>Auth finished</h3>
    <p>아래 토큰을 앱(Flutter)에서 Authorization Bearer로 사용하면 된다.</p>
    <textarea style="width: 100%; height: 180px;">{token}</textarea>
  </body>
</html>
"""
    return HTMLResponse(html, status_code=200)
