from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests, os
from datetime import datetime

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

def yt_get(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/search")
def search(query: str, start: str, end: str):
    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults=25"
        f"&q={query}"
        f"&publishedAfter={start}T00:00:00Z"
        f"&publishedBefore={end}T23:59:59Z"
        f"&key={YOUTUBE_API_KEY}"
    )

    data = yt_get(url)
    if "error" in data:
        return {"videos": [], "total": 0, "error": data["error"]}

    video_ids = [i["id"]["videoId"] for i in data.get("items", [])]

    stats_url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=statistics,snippet&id={','.join(video_ids)}"
        f"&key={YOUTUBE_API_KEY}"
    )

    stats = yt_get(stats_url)
    videos = []

    for v in stats.get("items", []):
        s = v["statistics"]
        sn = v["snippet"]
        videos.append({
            "title": sn["title"],
            "channel": sn["channelTitle"],
            "published": sn["publishedAt"][:10],
            "views": int(s.get("viewCount", 0)),
            "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0)),
        })

    return {"videos": videos, "total": len(videos)}
