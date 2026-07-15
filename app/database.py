from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== KONFIGURASI DATABASE ====================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "smart_blindstick")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    """Connect ke MongoDB Atlas (Cloud)"""
    try:
        db.client = AsyncIOMotorClient(MONGO_URI)
        db.db = db.client[DATABASE_NAME]
        print("✅ Connected to MongoDB Atlas!")
        
        # Buat index untuk query cepat
        await db.db.sensor_data.create_index("device_id")
        await db.db.sensor_data.create_index("timestamp")
        await db.db.sensor_data.create_index([("gps.latitude", 1), ("gps.longitude", 1)])
        await db.db.alert_logs.create_index("device_id")
        await db.db.alert_logs.create_index("timestamp")
        await db.db.alert_logs.create_index("acknowledged")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("🔌 MongoDB connection closed")

def get_database():
    return db.db