import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import config

app = FastAPI(title="Deshi Video Streaming")

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Static mount failed: {e}")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {"status": "ok", "bot": config.BOT_NAME}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/watch/{token}", response_class=HTMLResponse)
async def watch(request: Request, token: str):
    return templates.TemplateResponse("ad_gate.html", {
        "request": request,
        "token": token,
        "ad_duration": config.AD_DURATION,
        "title": "Video"
    })


@app.get("/video/{token}")
async def video(token: str):
    return {"message": "Video endpoint works"}
