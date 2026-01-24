import os
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from security import create_access_token

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# 중요: 구글 로그인 후 돌아갈 URL
# - Flutter Web/앱이 아직 없으면, 서버에 finish 페이지를 두고 거기로 보내는 게 제일 단순함
FRONTEND_REDIRECT_URI = os.getenv(
    "FRONTEND_REDIRECT_URI",
    "https://foodieserver-production.up.railway.app/auth/finish",
)

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
    # 서버는 떠야 하니, 실제 호출 시점에 에러를 던지는 방식으로 처리
    pass


@router.get("/auth/google/login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth env vars missing")

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
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth env vars missing")

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

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"Failed to get access token: {token_data}")

    # 2) access_token -> userinfo
    async with httpx.AsyncClient(timeout=15.0) as http:
        user_res = await http.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    user_info = user_res.json()

    email = user_info.get("email")
    name = user_info.get("name", "")
    if not email:
        raise HTTPException(status_code=400, detail=f"Failed to get user info: {user_info}")

    user_id = email  # 임시로 email을 user_id로 사용
    jwt_token = create_access_token({"sub": user_id, "email": email, "name": name})

    # 3) 프론트(또는 서버 finish 페이지)로 이동
    redirect_url = f"{FRONTEND_REDIRECT_URI}?token={jwt_token}"
    return RedirectResponse(url=redirect_url, status_code=307)


@router.get("/auth/finish", response_class=HTMLResponse)
def auth_finish(token: Optional[str] = None):
    # Flutter가 아직 없으면 여기서 토큰을 눈으로 확인/복사 가능하게 해둔다.
    if not token:
        return HTMLResponse(
            "<h3>Auth finished</h3><p>Missing token</p>",
            status_code=400,
        )

    html = f"""
    <html>
      <head><meta charset="utf-8"/></head>
      <body style="font-family: Arial, sans-serif; padding: 24px;">
        <h2>Google Login Success</h2>
        <p>아래 토큰을 복사해서 Authorization 헤더에 넣으면 /analyze를 테스트할 수 있음.</p>
        <pre style="white-space: pre-wrap; word-break: break-all; padding: 12px; background: #f2f2f2;">{token}</pre>
      </body>
    </html>
    """
    return HTMLResponse(html, status_code=200)
