from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from fetch_and_store import get_collection
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def initial_ingestion(channel_name: str, limit=10):
    options = {
        'quiet': False,
        'extract_flat': True,
        'playlistend': limit
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/@{channel_name}/videos", download=False)
        docs = []
        for entry in info['entries']:
            doc = {
                'channel_name': channel_name,
                'video_id': entry.get('id'),
                'title': entry.get('title'),
                'url': entry.get('url'),
                'upload_date': entry.get('upload_date'),
                'view_count': entry.get('view_count', 0),
                'like_count': entry.get('like_count', 0),
                'description': entry.get('description')
            }
            docs.append(doc)
        if docs:
            get_collection().insert_many(docs)
    return "Metadata uploaded successfully!"

try:
    initial_ingestion("ANINewsIndia")
except Exception as e:
    print(e)