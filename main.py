from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/search")
def search(query: str, start: str, end: str):
    search_url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults=1000"
        f"&q={query}"
        f"&publishedAfter={start}T00:00:00Z"
        f"&publishedBefore={end}T23:59:59Z"
        f"&key={API_KEY}"
    )

    search_res = requests.get(search_url, timeout=30).json()

    video_ids = []
    for item in search_res.get("items", []):
        video_ids.append(item["id"]["videoId"])

    if not video_ids:
        return {"videos": [], "total": 0}

    stats_url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=statistics,snippet"
        f"&id={','.join(video_ids)}"
        f"&key={API_KEY}"
    )

    stats_res = requests.get(stats_url, timeout=30).json()

    videos = []

    for v in stats_res.get("items", []):
        snippet = v["snippet"]
        stats = v.get("statistics", {})

        videos.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "published": snippet["publishedAt"][:10],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
        })

    return {
        "videos": videos,
        "total": len(videos)
    }
