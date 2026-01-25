from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# routers 패키지에서 import (정답)
from routers.meals import router as meals_router
from routers.profile import router as profile_router
from routers.summary import router as summary_router

app = FastAPI(
    title="Foodie API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(meals_router)
app.include_router(profile_router)
app.include_router(summary_router)

@app.get("/")
def health_check():
    return {"status": "ok"}
