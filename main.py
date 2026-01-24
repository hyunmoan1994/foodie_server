from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router
from routers.auth_dev import router as auth_dev_router
from auth_google import router as google_router

app = FastAPI(title="Foodie Server", version="0.2.0")

# CORS (일단 개발 편의상 전체 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Routers
app.include_router(analyze_router)
app.include_router(auth_dev_router)
app.include_router(google_router)
