from fastapi import APIRouter
from pydantic import BaseModel

from security import create_access_token

router = APIRouter()


class DevLoginRequest(BaseModel):
    email: str = "dev@example.com"
    user_id: str = "dev-user"


@router.post("/auth/dev/login")
def dev_login(req: DevLoginRequest):
    token = create_access_token({"sub": req.user_id, "email": req.email})
    return {"token": token}
