from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 파일 단위 import (중요)
import meals
import profile
import summary

app = FastAPI(
    title="Foodie API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ router 직접 참조
app.include_router(meals.router)
app.include_router(profile.router)
app.include_router(summary.router)

@app.get("/")
def health_check():
    return {"status": "ok"}
