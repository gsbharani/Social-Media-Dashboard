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
def search(
    query: str,
    start: str,
    end: str,
    page_token: str | None = None
):
    # 1️⃣ SEARCH VIDEOS (50 per request – YouTube limit)
    search_params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "publishedAfter": f"{start}T00:00:00Z",
        "publishedBefore": f"{end}T23:59:59Z",
        "maxResults": 50,
        "key": API_KEY
    }

    if page_token:
        search_params["pageToken"] = page_token

    search_res = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params=search_params,
        timeout=30
    ).json()

    video_ids = [
        item["id"]["videoId"]
        for item in search_res.get("items", [])
        if item["id"].get("videoId")
    ]

    if not video_ids:
        return {
            "videos": [],
            "nextPageToken": None,
            "total": 0
        }

    # 2️⃣ FETCH STATS
    stats_res = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "statistics,snippet",
            "id": ",".join(video_ids),
            "key": API_KEY
        },
        timeout=30
    ).json()

    videos = []
    for v in stats_res.get("items", []):
        s = v["snippet"]
        st = v.get("statistics", {})

        videos.append({
            "title": s["title"],
            "channel": s["channelTitle"],
            "published": s["publishedAt"][:10],
            "views": int(st.get("viewCount", 0)),
            "likes": int(st.get("likeCount", 0)),
            "comments": int(st.get("commentCount", 0)),
            "url": f"https://www.youtube.com/watch?v={v['id']}"
        })

    return {
        "videos": videos,
        "nextPageToken": search_res.get("nextPageToken"),
        "total": len(videos)
    }
