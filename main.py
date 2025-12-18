from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError("Set YOUTUBE_API_KEY environment variable")

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
    page_token: str = Query(None)
):
    # Search videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "maxResults": 50,  # API max per request
        "publishedAfter": f"{start}T00:00:00Z",
        "publishedBefore": f"{end}T23:59:59Z",
        "key": API_KEY
    }
    if page_token:
        search_params["pageToken"] = page_token

    res = requests.get(search_url, params=search_params, timeout=30).json()

    video_ids = [item["id"]["videoId"] for item in res.get("items", [])]
    next_page_token = res.get("nextPageToken")

    videos = []
    if video_ids:
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": API_KEY
        }
        stats_res = requests.get(stats_url, params=stats_params, timeout=30).json()

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
                "url": f"https://www.youtube.com/watch?v={v['id']}"
            })

    return {
        "videos": videos,
        "nextPageToken": next_page_token
    }
