from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ routers 폴더 기준 import
from routers import meals
from routers import profile
from routers import summary

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

# ✅ router 등록
app.include_router(meals.router)
app.include_router(profile.router)
app.include_router(summary.router)

@app.get("/")
def health_check():
    return {"status": "ok"}
