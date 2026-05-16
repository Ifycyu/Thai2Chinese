from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.routers import analyze, tts, api, translate, learn, async_tasks

app = FastAPI(title="ThaiWord - Thai Language Learning Tool")
    
# Internal API (for frontend)
app.include_router(analyze.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(translate.router, prefix="/api")
app.include_router(learn.router, prefix="/api")
app.include_router(async_tasks.router, prefix="/api")

# External API (for third-party)
app.include_router(api.router, prefix="/api")

static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(static_dir / "index.html"))


@app.get("/translate.html")
async def translate_page():
    return FileResponse(str(static_dir / "translate.html"))


@app.get("/settings.html")
async def settings_page():
    return FileResponse(str(static_dir / "settings.html"))


@app.get("/api-docs.html")
async def api_docs_page():
    return FileResponse(str(static_dir / "api-docs.html"))


@app.get("/learn.html")
async def learn_page():
    return FileResponse(str(static_dir / "learn.html"))
