import time
from collections import defaultdict
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from app.services.tts_service import generate_tts

router = APIRouter(tags=["tts"])

# Simple per-IP rate limiter: max 30 requests per 60 seconds
_tts_rate_limit: dict[str, list[float]] = defaultdict(list)
_TTS_MAX_REQUESTS = 30
_TTS_WINDOW_SECONDS = 60


def _check_rate_limit(ip: str):
    now = time.time()
    window_start = now - _TTS_WINDOW_SECONDS
    # Clean old entries
    _tts_rate_limit[ip] = [t for t in _tts_rate_limit[ip] if t > window_start]
    if len(_tts_rate_limit[ip]) >= _TTS_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    _tts_rate_limit[ip].append(now)


@router.get("/tts/{word}")
async def tts(word: str, request: Request):
    if len(word) > 100:
        raise HTTPException(status_code=400, detail="单词过长")

    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    audio_path = await generate_tts(word)
    return FileResponse(audio_path, media_type="audio/mpeg")
