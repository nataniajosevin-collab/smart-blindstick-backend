from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import router
from app.database import connect_to_mongo, close_mongo_connection
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("🚀 SMART BLIND STICK BACKEND v2.0")
    print("=" * 60)
    try:
        await connect_to_mongo()
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
    print("✅ Backend ready!")
    print("=" * 60)
    yield
    # Shutdown
    await close_mongo_connection()
    print("👋 Shutting down...")

# ==================== INISIALISASI APP ====================
app = FastAPI(
    title="Smart Blind Stick API",
    description="API untuk monitoring tongkat pintar dengan tracking GPS",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== CORS MIDDLEWARE ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stick-blind-tuner.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== REGISTER ROUTER ====================
app.include_router(router, prefix="/api")

# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    return {
        "message": "Smart Blind Stick API",
        "status": "running",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ==================== JALANKAN (untuk local testing) ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )