import xmltodict
import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from fetch_and_store import fetch_and_store_video

app = FastAPI()

@app.get("/check-connection")
def check_connection():
    return {"message": "Connection successful"}

@app.get("/webhook", response_class=PlainTextResponse)
async def webhook_verify(hub_challenge: str = Query(..., alias="hub.challenge")):
    return hub_challenge

@app.post("/webhook")
async def webhook_notify(request: Request):
    body = await request.body()
    parsed_body = xmltodict.parse(body)
    entry = parsed_body.get("feed", {}).get("entry", {})
    video_id = entry.get("yt:videoId")
    if video_id:
        await fetch_and_store_video(video_id)
    return {"message": "Webhook notification received"}

if __name__ == "__main__":
    uvicorn.run("webhook_handler:app", host="0.0.0.0", port=8080, reload=True)