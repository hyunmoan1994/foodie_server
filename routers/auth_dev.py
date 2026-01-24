import os
from fastapi import APIRouter, HTTPException, Query

from security import issue_jwt

router = APIRouter(tags=["auth"])

@router.get("/auth/dev/token")
def dev_token(
    user: str = Query("dev_user"),
    email: str | None = Query(None),
):
    # Railway/운영에서 실수로 열리는 것을 막기 위한 안전장치
    enabled = os.getenv("DEV_AUTH_ENABLED", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=404, detail="Not Found")

    token = issue_jwt(sub=user, email=email)
    return {"access_token": token, "token_type": "bearer"}
