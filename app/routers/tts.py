from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.tts_service import generate_tts

router = APIRouter(tags=["tts"])


@router.get("/tts/{word}")
async def tts(word: str):
    audio_path = await generate_tts(word)
    return FileResponse(audio_path, media_type="audio/mpeg")
