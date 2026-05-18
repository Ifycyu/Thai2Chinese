"""TTS service with caching and cache eviction."""
import asyncio
import hashlib
import logging
import time
from pathlib import Path

import edge_tts

logger = logging.getLogger(__name__)

VOICE = "th-TH-PremwadeeNeural"
CACHE_DIR = Path(__file__).parent.parent / "data" / "audio_cache"
MAX_CACHE_SIZE_MB = 100  # Maximum cache size in MB
MAX_CACHE_AGE_DAYS = 7   # Maximum cache age in days

# Lock per file to avoid concurrent writes
_file_locks: dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()


async def _get_file_lock(key: str) -> asyncio.Lock:
    async with _locks_lock:
        if key not in _file_locks:
            _file_locks[key] = asyncio.Lock()
        return _file_locks[key]


def cleanup_cache():
    """Clean up old cache files."""
    if not CACHE_DIR.exists():
        return

    now = time.time()
    max_age = MAX_CACHE_AGE_DAYS * 86400
    total_size = 0
    files = []

    for f in CACHE_DIR.glob("*.mp3"):
        stat = f.stat()
        files.append((f, stat.st_mtime, stat.st_size))
        total_size += stat.st_size

    # Remove old files
    removed = 0
    for f, mtime, size in files:
        if now - mtime > max_age:
            f.unlink()
            removed += 1
            total_size -= size

    # If still too large, remove oldest files
    if total_size > MAX_CACHE_SIZE_MB * 1024 * 1024:
        files.sort(key=lambda x: x[1])  # Sort by modification time
        for f, mtime, size in files:
            if total_size <= MAX_CACHE_SIZE_MB * 1024 * 1024:
                break
            if f.exists():
                f.unlink()
                removed += 1
                total_size -= size

    if removed:
        logger.info(f"Cleaned up {removed} TTS cache files")


async def generate_tts(text: str) -> Path:
    """Generate TTS audio with caching."""
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
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(str(cache_path))
            logger.info(f"Generated TTS for: {text[:20]}...")
        except Exception as e:
            logger.error(f"TTS generation failed for '{text[:20]}...': {e}")
            raise

    return cache_path
