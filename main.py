from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI(title="Tamil Nadu Politics YouTube Dashboard")

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


@app.get("/tn-politics")
def tn_politics():
    keywords = [
        "Tamil Nadu politics",
        "DMK",
        "ADMK",
        "MK Stalin",
        "EPS",
        "Tamil Nadu government",
        "TN election"
    ]

    videos = []

    for kw in keywords:
        search_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&type=video&maxResults=5&q={kw}"
            f"&regionCode=IN&key={API_KEY}"
        )

        data = safe_get(search_url)
        if "error" in data:
            continue

        video_ids = [
            item["id"]["videoId"]
            for item in data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            continue

        stats_url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet,statistics&id={','.join(video_ids)}"
            f"&key={API_KEY}"
        )

        stats = safe_get(stats_url)
        if "error" in stats:
            continue

        for v in stats.get("items", []):
            sn = v.get("snippet", {})
            st = v.get("statistics", {})

            videos.append({
                "title": sn.get("title"),
                "channel": sn.get("channelTitle"),
                "published": sn.get("publishedAt", "")[:10],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "url": f"https://youtu.be/{v['id']}"
            })

    return JSONResponse({
        "videos": videos,
        "total": len(videos)
    })


@app.get("/")
def home():
    return FileResponse("static/index.html")
