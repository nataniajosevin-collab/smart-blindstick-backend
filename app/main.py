from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import router
from app.database import get_database, close_database
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 SMART BLIND STICK BACKEND v2.0")
    logger.info("=" * 60)
    
    # Test database connection
    try:
        db = get_database()
        if db:
            logger.info("✅ Database connected!")
        else:
            logger.warning("⚠️ Database not connected!")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
    
    logger.info("✅ Backend ready!")
    yield
    
    # Shutdown
    close_database()
    logger.info("👋 Shutting down...")

# ==================== APP ====================
app = FastAPI(
    title="Smart Blind Stick API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs"
)

# CORS
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

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Smart Blind Stick API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2026-07-15T23:30:00"}