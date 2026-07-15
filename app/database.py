import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://nataniajosevin_db_user:x4NE!UGYdtfL7%23S@cluster0.o4uxoky.mongodb.net/?appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "smart_blindstick")

client = None
db = None

def get_database():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DATABASE_NAME]
    return db

def close_database():
    global client
    if client:
        client.close()