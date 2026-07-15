import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import get_database, close_database

app = FastAPI(
    title=os.getenv("APP_NAME", "Smart Blind Stick API"),
    version=os.getenv("APP_VERSION", "2.0.0")
)

# Mengizinkan akses dari browser (HTML lokal maupun hosting luar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    db = get_database()
    print("🚀 Server Started & MongoDB Atlas Integration Connected Successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    close_database()

# Daftarkan router utama dengan prefix /api agar menjadi /api/sensors
app.include_router(router, prefix="/api")