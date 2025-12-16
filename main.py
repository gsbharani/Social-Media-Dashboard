from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError("Set YOUTUBE_API_KEY")

app = FastAPI(title="YouTube Video Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Helper
# ---------------------------
def yt(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# ---------------------------
# Search YouTube
# ---------------------------
@app.get("/videos")
def get_videos(query: str, start: str, end: str, max_results: int = 500):
    query = query.lstrip("#").strip()
    if not query:
        raise HTTPException(400, "Query required")

    video_ids = []
    next_page = ""

    while len(video_ids) < max_results:
        url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&type=video&maxResults=50&q={query}"
            f"&publishedAfter={start}T00:00:00Z"
            f"&publishedBefore={end}T23:59:59Z"
            f"&pageToken={next_page}&key={API_KEY}"
        )
        data = yt(url)

        for item in data.get("items", []):
            video_ids.append(item["id"]["videoId"])
            if len(video_ids) >= max_results:
                break

        next_page = data.get("nextPageToken")
        if not next_page:
            break

    if not video_ids:
        return {"videos": []}

    stats = []
    for i in range(0, len(video_ids), 50):
        batch = ",".join(video_ids[i:i+50])
        info = yt(
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet,statistics&id={batch}&key={API_KEY}"
        )

        for v in info.get("items", []):
            s = v["snippet"]
            st = v.get("statistics", {})
            stats.append({
                "title": s["title"],
                "channel": s["channelTitle"],
                "published": s["publishedAt"][:10],
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
