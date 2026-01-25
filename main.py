from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router
from routers.auth_dev import router as auth_dev_router
from auth_google import router as google_router  # 네 프로젝트에 있는 auth_google.py 기준

app = FastAPI(title="Foodie Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 운영에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- 기본 경로
app.include_router(google_router)
app.include_router(auth_dev_router)
app.include_router(analyze_router)

# ---- /api 호환 경로 (선택이지만, 네가 이미 쓰고 있어서 유지)
app.include_router(google_router, prefix="/api")
app.include_router(auth_dev_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
