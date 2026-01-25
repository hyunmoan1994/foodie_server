from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router
from routers.auth_dev import router as auth_dev_router
from auth_google import router as google_router  # 기존 파일이 auth_google.py 라는 전제

app = FastAPI(title="Foodie Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 운영 시에는 앱 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ 라우터 등록 (이게 빠지면 /analyze 가 404로 뜸)
app.include_router(google_router)
app.include_router(auth_dev_router)
app.include_router(analyze_router)

# ✅ 호환용: 앱/클라가 /api/... 로 때려도 동작하게 같이 열어둠 (선택이지만 강력 추천)
app.include_router(google_router, prefix="/api")
app.include_router(auth_dev_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
