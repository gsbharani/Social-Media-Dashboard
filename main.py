from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI(title="YouTube Data Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


def safe_get(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/search")
def search_videos(query: str, start: str, end: str, max_results: int = 500):
    if not query:
        raise HTTPException(400, "Query required")

    videos = []
    next_page = ""

    while len(videos) < max_results:
        search_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&type=video&maxResults=50&q={query}"
            f"&publishedAfter={start}T00:00:00Z"
            f"&publishedBefore={end}T23:59:59Z"
            f"&regionCode=IN&pageToken={next_page}&key={API_KEY}"
        )

        data = safe_get(search_url)
        if "error" in data:
            break

        ids = [i["id"]["videoId"] for i in data.get("items", [])]
        if not ids:
            break

        stats_url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet,statistics&id={','.join(ids)}&key={API_KEY}"
        )

        stats = safe_get(stats_url)
        if "error" in stats:
            break

        for v in stats.get("items", []):
            sn = v["snippet"]
            st = v.get("statistics", {})
            videos.append({
                "title": sn["title"],
                "channel": sn["channelTitle"],
                "published": sn["publishedAt"][:10],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "url": f"https://youtu.be/{v['id']}"
            })

        next_page = data.get("nextPageToken", "")
        if not next_page:
            break

    return JSONResponse({"videos": videos, "total": len(videos)})


@app.get("/")
def home():
    return FileResponse("static/index.html")
