import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

def get_collection():
    client = MongoClient(MONGO_URI)
    db = client["youtube_videos"]
    return db["videos"]

async def fetch_and_store_video(video_id: str):
    client = httpx.AsyncClient()
    response = await client.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params = {
            "part": "snippet,statistics",
            "id": video_id,
            "key": YOUTUBE_API_KEY,
        },
        timeout = 10,
    )
    await client.aclose()
    data = response.json()

    if not data.get("items"):
        return

    item = data["items"][0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})

    doc = {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "upload_date": snippet.get("publishedAt", ""),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "description": snippet.get("description", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_name": snippet.get("channelTitle", ""),
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }

    get_collection().insert_one(doc)