from fastapi import APIRouter
from pydantic import BaseModel

from security import create_access_token

router = APIRouter(prefix="/auth/dev", tags=["auth-dev"])


class DevLoginRequest(BaseModel):
    email: str
    user_id: str


@router.post("/login")
def dev_login(req: DevLoginRequest):
    """
    개발/테스트용 로그인.
    운영에서는 제거하거나 IP 제한/비활성 권장.
    """
    token = create_access_token(subject=req.user_id, email=req.email)
    return {"token": token}
