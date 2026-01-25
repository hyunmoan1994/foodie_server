from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import engine, Base
from routers.analyze import router as analyze_router
from routers.meals import router as meals_router

# 기존에 쓰던 auth 라우터들이 있다면 유지
from routers.auth_dev import router as auth_dev_router
from auth_google import router as google_router  # 너 프로젝트 구조에 맞춰 유지

app = FastAPI(title="Foodie Server", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

# 라우터 등록
app.include_router(auth_dev_router)
app.include_router(google_router)

app.include_router(analyze_router)
app.include_router(meals_router)
