import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Header, HTTPException
import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30일 기본

def create_access_token(subject: str, email: Optional[str] = None, expires_minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    exp_mins = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES

    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": now + timedelta(minutes=exp_mins),
    }
    if email:
        payload["email"] = email

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(...)) -> Dict[str, Any]:
    # Railway/브라우저/앱 모두 "Authorization: Bearer <token>" 형태
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)

    # 최소 필드만 반환 (DB 붙기 전 단계)
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "payload": payload,
    }
