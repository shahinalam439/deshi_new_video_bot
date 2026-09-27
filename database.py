from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DB_NAME]
series_col = db["series"]
episodes_col = db["episodes"]
users_col = db["users"]

async def create_series(title, description, poster_url, genres, year):
    doc = {"title": title, "description": description, "poster_url": poster_url,
           "genres": genres, "year": year, "created_at": datetime.utcnow()}
    r = await series_col.insert_one(doc)
    return str(r.inserted_id)

async def get_series_by_name(name):
    return await series_col.find_one({"title": {"$regex": name, "$options": "i"}})

async def get_series_by_id(sid):
    try:
        return await series_col.find_one({"_id": ObjectId(sid)})
    except Exception:
        return None

async def list_all_series(limit=50):
    return await series_col.find().sort("created_at", -1).to_list(limit)

async def delete_series(sid):
    await episodes_col.delete_many({"series_id": sid})
    await series_col.delete_one({"_id": ObjectId(sid)})

async def add_episode(series_id, season, ep_num, title, file_id, file_uid):
    doc = {"series_id": series_id, "season": season, "episode_num": ep_num,
           "title": title, "file_id": file_id, "file_unique_id": file_uid,
           "views": 0, "created_at": datetime.utcnow()}
    r = await episodes_col.insert_one(doc)
    return str(r.inserted_id)

async def get_episodes(series_id):
    return await episodes_col.find({"series_id": series_id}).sort(
        [("season", 1), ("episode_num", 1)]).to_list(500)

async def get_episode_by_id(eid):
    try:
        return await episodes_col.find_one({"_id": ObjectId(eid)})
    except Exception:
        return None

async def increment_views(eid):
    await episodes_col.update_one({"_id": ObjectId(eid)}, {"$inc": {"views": 1}})

async def save_user(uid, username, first_name):
    await users_col.update_one({"user_id": uid},
        {"$set": {"username": username, "first_name": first_name,
                  "last_seen": datetime.utcnow()}}, upsert=True)

async def get_total_users():
    return await users_col.count_documents({})

async def get_all_user_ids():
    users = await users_col.find({}, {"user_id": 1}).to_list(200000)
    return [u["user_id"] for u in users]

async def get_total_series():
    return await series_col.count_documents({})

async def get_total_episodes():
    return await episodes_col.count_documents({})

async def get_total_views():
    r = await episodes_col.aggregate(
        [{"$group": {"_id": None, "total": {"$sum": "$views"}}}]).to_list(1)
    return r[0]["total"] if r else 0
