"""ThaiWord FastAPI application."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.logger import setup_logging
from app.routers import analyze, tts, api, async_tasks
from app.services.dictionary import dictionary

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    setup_logging()
    logger.info("ThaiWord server starting...")

    async def periodic_save():
        while True:
            await asyncio.sleep(300)
            dictionary.save()
            logger.debug("Dictionary cache saved")

    async def cleanup_expired_tasks():
        from app.routers.async_tasks import cleanup_tasks
        await cleanup_tasks()

    asyncio.create_task(periodic_save())
    asyncio.create_task(cleanup_expired_tasks())

    yield

    # Shutdown
    dictionary.save()
    logger.info("ThaiWord server stopped")


app = FastAPI(
    title="ThaiWord - Thai Language Learning Tool",
    description="泰语学习助手：分词、释义、声调分析、发音",
    version="1.0.0",
    lifespan=lifespan,
)


# ========== Global Exception Handler ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return JSON."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ========== Register Routers ==========
app.include_router(analyze.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(async_tasks.router, prefix="/api")
app.include_router(api.router, prefix="/api")

# ========== Static Files ==========
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ========== Page Routes ==========
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


# ========== Health Check ==========
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
