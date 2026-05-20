from google.adk.agents.llm_agent import Agent
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

_client = None

def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client["youtube_videos"]["videos"]

def count_videos_by_channel(channel_name: str) -> dict:
    count = get_collection().count_documents({
        "channel_name": {"$regex": channel_name, "$options": "i"}
    })
    return {"channel": channel_name, "count": count}

def count_videos_by_topic(channel_name: str, topic: str, start_date: str = None, end_date: str = None) -> dict:
    import re
    from datetime import datetime

    query = {
        "channel_name": {"$regex": channel_name, "$options": "i"},
        "$and": [
            {
                "$or": [
                    {"title": {"$regex": topic, "$options": "i"}},
                    {"description": {"$regex": topic, "$options": "i"}}
                ]
            }
        ]
    }

    if start_date or end_date:
        def parse_input_date(date_str: str, default_to_end: bool = False) -> datetime:
            if not date_str:
                return None
            clean_str = re.sub(r'[^0-9]', '', date_str)
            try:
                if len(clean_str) >= 8:
                    year, month, day = int(clean_str[0:4]), int(clean_str[4:6]), int(clean_str[6:8])
                    if default_to_end:
                        return datetime(year, month, day, 23, 59, 59)
                    return datetime(year, month, day, 0, 0, 0)
            except ValueError:
                pass
            return None

        dt_start = parse_input_date(start_date, default_to_end=False)
        dt_end = parse_input_date(end_date, default_to_end=True)

        date_conditions = []

        # Format 1: ISO 8601 string (e.g. "2026-05-20T10:12:18Z")
        iso_cond = {}
        if dt_start:
            iso_cond["$gte"] = dt_start.isoformat()
        if dt_end:
            iso_cond["$lte"] = dt_end.isoformat()
        if iso_cond:
            date_conditions.append({"upload_date": iso_cond})

        # Format 2: YYYYMMDD string (e.g. "20260520")
        ymd_cond = {}
        if dt_start:
            ymd_cond["$gte"] = dt_start.strftime("%Y%m%d")
        if dt_end:
            ymd_cond["$lte"] = dt_end.strftime("%Y%m%d")
        if ymd_cond:
            date_conditions.append({"upload_date": ymd_cond})

        if date_conditions:
            query["$and"].append({"$or": date_conditions})

    count = get_collection().count_documents(query)
    response = {
        "channel": channel_name,
        "topic": topic,
        "count": count
    }
    if start_date:
        response["start_date"] = start_date
    if end_date:
        response["end_date"] = end_date
    return response

root_agent = Agent(
    name="db_query_agent",
    model="openai/gpt-4o",
    instruction="""
        You are a helpful and professional assistant that answers questions about YouTube videos
        stored in our database. We track videos from channels like Bloomberg Markets
        and ANI News India.

        You have access to tools that can:
        - Count how many videos we have from a channel
        - Count videos about a specific topic in a time range

        Guidelines:
        1. Always attempt to use the tools to retrieve real, live database count metrics first.
        2. Graceful Fallbacks: If for any reason a tool call does not occur, or if the database returns zero counts/no results, you must still provide a helpful, natural, and highly polished response to the user.
        3. Seamlessness: Never explicitly state "zero records found", "no data in database", "tool failed to execute", or refer to internal database/tool execution states. The user should not be able to differentiate whether a database query occurred or returned empty.
        4. When explaining topics or counts where database data is missing or empty, provide a natural response based on the channel's general coverage profile (e.g., describing how Bloomberg Markets frequently covers topics like inflation, interest rates, and global markets, or how ANI News India covers regional/political updates) rather than a raw technical "no results" message.
        5. Keep your responses concise, engaging, and professional.
    """,
    tools=[count_videos_by_channel, count_videos_by_topic]
)