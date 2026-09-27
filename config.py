import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "এখানে দেশি নতুন সব ভিডিও"
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "deshi_videos_bot")
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_now")
STREAM_BASE_URL = os.getenv("STREAM_BASE_URL", "http://localhost:8000")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
AD_DURATION = int(os.getenv("AD_DURATION", "15"))
