import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME", "thinkbreath")

client = MongoClient(MONGO_URL)
db     = client[DB_NAME]

users             = db["users"]
habits            = db["habits"]
habit_completions = db["habit_completions"]
sessions          = db["sessions"]
