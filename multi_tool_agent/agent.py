from google.adk.agents.llm_agent import Agent
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def get_collection():
    client = MongoClient(MONGO_URI)
    db = client["youtube_videos"]
    return db["videos"]

def count_videos_by_channel(channel_name: str) -> dict:
    count = get_collection().count_documents({
        "channel_title": {"$regex": channel_name, "$options": "i"}
    })
    return {"channel": channel_name, "count": count}

def count_videos_by_topic(channel_name: str, topic: str) -> dict:
    count = get_collection().count_documents({
        "channel_title": {"$regex": channel_name, "$options": "i"},
        "$or": [
            {"title": {"$regex": topic, "$options": "i"}},
            {"description": {"$regex": topic, "$options": "i"}}
        ]
    })
    return {"channel": channel_name, "topic": topic, "count": count}

root_agent = Agent(
    name="db_query_agent",
    model="gemini-2.5-flash",
    instruction="""
        You are a helpful assistant that answers questions about YouTube videos
        stored in our database. We track videos from channels like Bloomberg Markets
        and ANI News India.

        You have access to tools that can:
        - Count how many videos we have from a channel
        - Count videos about a specific topic in a time range

        Always use the tools to get real data before answering.
        Be concise and clear in your responses.
    """,
    tools=[count_videos_by_channel, count_videos_by_topic]
)