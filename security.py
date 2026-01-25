import os
import time
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer


# =====================
# Env
# =====================
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if not SECRET_KEY:
    # Railway에서 SECRET_KEY 미설정이면 dev 모드 토큰도 흔들리기 때문에
    # 명확히 에러를 발생시키는 게 낫다.
    raise RuntimeError("SECRET_KEY environment variable is not set.")


# =====================
# OAuth2 Bearer
# =====================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(
    *,
    subject: str,
    email: Optional[str] = None,
    expires_minutes: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    JWT access token 생성.
    - subject: user_id (sub claim)
    - email: optional
    - expires_minutes: optional (기본 ENV)
    """
    exp_min = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": int(time.time()) + exp_min * 60,
    }
    if email:
        payload["email"] = email
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return decode_token(token)
