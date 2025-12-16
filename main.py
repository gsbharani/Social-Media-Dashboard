from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError("Set YOUTUBE_API_KEY in .env")

app = FastAPI(title="YouTube Analytics Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# YouTube API Helper
# ---------------------------
def yt_get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# ---------------------------
# Trending Videos (Region)
# ---------------------------
@app.get("/trending")
def trending_videos(region="US", max_results: int = 50):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={region}&maxResults={max_results}&key={API_KEY}"
    data = yt_get(url)
    videos = []
    for v in data.get("items", []):
        sn, st = v["snippet"], v.get("statistics", {})
        videos.append({
            "title": sn["title"],
            "channel": sn["channelTitle"],
            "published": sn["publishedAt"][:10],
            "views": int(st.get("viewCount", 0)),
            "likes": int(st.get("likeCount", 0)),
            "comments": int(st.get("commentCount", 0)),
            "url": f"https://youtu.be/{v['id']}"
        })
    return {"videos": videos}

# ---------------------------
# Search Videos by Keyword & Date
# ---------------------------
@app.get("/search")
def search_videos(query: str = "", start: str = "", end: str = "", max_results: int = 50):
    if not query:
        return {"videos": []}

    video_ids = []
    next_page = ""
    while len(video_ids) < max_results:
        url = (
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=50&q={query}"
            f"&publishedAfter={start}T00:00:00Z&publishedBefore={end}T23:59:59Z&pageToken={next_page}&key={API_KEY}"
        )
        data = yt_get(url)
        for item in data.get("items", []):
            video_ids.append(item["id"]["videoId"])
            if len(video_ids) >= max_results:
                break
        next_page = data.get("nextPageToken")
        if not next_page:
            break

    stats = []
    for i in range(0, len(video_ids), 50):
        batch = ",".join(video_ids[i:i+50])
        info = yt_get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={batch}&key={API_KEY}")
        for v in info.get("items", []):
            sn, st = v["snippet"], v.get("statistics", {})
            stats.append({
                "title": sn["title"],
                "channel": sn["channelTitle"],
                "published": sn["publishedAt"][:10],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "url": f"https://youtu.be/{v['id']}"
            })
    return {"videos": stats}

# ---------------------------
# Serve Frontend
# ---------------------------
@app.get("/", include_in_schema=False)
def home():
    return FileResponse("static/index.html")
