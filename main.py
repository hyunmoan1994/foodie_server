from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router
from routers.auth_dev import router as auth_dev_router
from auth_google import router as google_router  # auth_google.py의 router

app = FastAPI(title="Foodie Server", version="0.1.0")

# CORS (앱/웹 붙을거라 일단 열어둠)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# ===== 라우터 등록 (이게 핵심) =====
app.include_router(google_router)      # /auth/google/login, /auth/google/callback, /auth/finish
app.include_router(analyze_router)     # /api/... 라우팅이면 analyze_router 내부 prefix 확인
app.include_router(auth_dev_router)    # 개발용 auth 있으면 유지
