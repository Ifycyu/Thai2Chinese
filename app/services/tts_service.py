import hashlib
from pathlib import Path
import edge_tts

VOICE = "th-TH-PremwadeeNeural"
CACHE_DIR = Path(__file__).parent.parent / "data" / "audio_cache"


async def generate_tts(text: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.md5(f"{VOICE}:{text}".encode()).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.mp3"

    if cache_path.exists():
        return cache_path

    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(cache_path))
    return cache_path
