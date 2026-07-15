import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "smart_blindstick")

class Database:
    client = None
    db = None

db = Database()

def get_database():
    """Get database connection"""
    global db
    
    if db.client is None:
        if not MONGO_URI:
            print("❌ MONGO_URI not set!")
            return None
        
        try:
            print(f"📡 Connecting to MongoDB...")
            db.client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db.db = db.client[DATABASE_NAME]
            
            # Test connection
            db.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas!")
            print(f"📊 Database: {DATABASE_NAME}")
            
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            print("⚠️ Running without database!")
            return None
    
    return db.db

def close_database():
    """Close database connection"""
    global db
    if db.client:
        db.client.close()
        db.client = None
        db.db = None
        print("🔌 MongoDB connection closed")