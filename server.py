import os
import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from pyrogram import Client
import config
import database as db

session_b64 = os.getenv("PYROGRAM_SESSION")
if session_b64:
    try:
        with open("stream_session.session", "wb") as f:
            f.write(base64.b64decode(session_b64))
    except Exception as e:
        print(f"Session restore failed: {e}")

app = FastAPI(title="Deshi Video Streaming")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

tg = Client(
    "stream_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    in_memory=False
)

@app.on_event("startup")
async def on_start():
    await tg.start()
    print("✅ Pyrogram started")

@app.on_event("shutdown")
async def on_stop():
    await tg.stop()

def decode(token):
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired link")

@app.get("/watch/{token}", response_class=HTMLResponse)
async def watch(request: Request, token: str):
    p = decode(token)
    ep = await db.get_episode_by_id(p["episode_id"])
    title = ep["title"] if ep else "Video"
    return templates.TemplateResponse("ad_gate.html", {
        "request": request, "token": token,
        "ad_duration": config.AD_DURATION, "title": title})

@app.get("/video/{token}")
async def video(token: str):
    p = decode(token)
    fid = p["file_id"]
    if p.get("episode_id"):
        try:
            await db.increment_views(p["episode_id"])
        except Exception:
            pass
    async def gen():
        async for chunk in tg.stream_media(fid):
            yield chunk
    return StreamingResponse(gen(), media_type="video/mp4",
                             headers={"Cache-Control": "no-cache"})

@app.get("/health")
async def health():
    return {"status": "ok"}
