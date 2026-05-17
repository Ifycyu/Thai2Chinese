import hashlib
import asyncio
from pathlib import Path
import edge_tts

VOICE = "th-TH-PremwadeeNeural"
CACHE_DIR = Path(__file__).parent.parent / "data" / "audio_cache"

# Lock per file to avoid concurrent writes to the same file
_file_locks: dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()


async def _get_file_lock(key: str) -> asyncio.Lock:
    async with _locks_lock:
        if key not in _file_locks:
            _file_locks[key] = asyncio.Lock()
        return _file_locks[key]


async def generate_tts(text: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.md5(f"{VOICE}:{text}".encode()).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.mp3"

    if cache_path.exists():
        return cache_path

    # Use per-file lock to avoid duplicate generation
    file_lock = await _get_file_lock(cache_key)
    async with file_lock:
        # Double-check after acquiring lock
        if cache_path.exists():
            return cache_path
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(str(cache_path))
    return cache_path
