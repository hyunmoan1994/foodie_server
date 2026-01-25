from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 import
from meals import router as meals_router
from profile import router as profile_router
from summary import router as summary_router

app = FastAPI(
    title="Foodie API",
    version="1.0.0",
)

# CORS (Flutter 앱 대응)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 나중에 앱 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 핵심 ===
# 실제 API 등록
app.include_router(meals_router)
app.include_router(profile_router)
app.include_router(summary_router)


@app.get("/")
def health_check():
    return {"status": "ok"}
