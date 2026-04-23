import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise Exception("Missing MONGO_URI or DB_NAME in .env")

client = MongoClient(MONGO_URI)

db = client[DB_NAME]

# Collections
users_collection = db["users"]
tasks_collection = db["tasks"]