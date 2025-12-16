from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests, os


API_KEY = os.getenv("YOUTUBE_API_KEY")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
return FileResponse("static/index.html")


@app.get("/search")
def search(query: str, start: str, end: str):
url = (
"https://www.googleapis.com/youtube/v3/search"
f"?part=snippet&type=video&maxResults=25"
f"&q={query}"
f"&publishedAfter={start}T00:00:00Z"
f"&publishedBefore={end}T23:59:59Z"
f"&key={API_KEY}"
)


r = requests.get(url, timeout=30).json()
video_ids = [i['id']['videoId'] for i in r.get('items', [])]


if not video_ids:
return {"videos": [], "total": 0}


stats_url = (
"https://www.googleapis.com/youtube/v3/videos"
f"?part=statistics,snippet&id={','.join(video_ids)}"
f"&key={API_KEY}"
)


stats = requests.get(stats_url, timeout=30).json()
videos = []


for v in stats.get('items', []):
s = v['statistics']
sn = v['snippet']
videos.append({
"title": sn['title'],
"channel": sn['channelTitle'],
"published": sn['publishedAt'][:10],
"views": int(s.get('viewCount', 0)),
"likes": int(s.get('likeCount', 0)),
"comments": int(s.get('commentCount', 0))
})


return {"videos": videos, "total": len(videos)}
