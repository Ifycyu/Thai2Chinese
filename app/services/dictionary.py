"""Dictionary service with caching and API fallback."""
import json
import logging
import re
import ssl
import time
import threading
import urllib.request
import urllib.parse
from pathlib import Path

from app.utils.url_validator import validate_dict_api_url, build_url_with_ip

logger = logging.getLogger(__name__)

CLASS_MAP = {
    "น.": "名词", "ก.": "动词", "ว.": "形容词", "สรร.": "代词", "สรรพ.": "代词",
    "วิ.": "副词", "สัน.": "连词", "อ.": "感叹词", "อุ.": "感叹词", "ล.": "量词",
    "บุ.": "介词", "อนุ.": "助词",
}

DICT_PATH = Path(__file__).parent.parent / "data" / "thai_chinese_dict.json"


class Dictionary:
    def __init__(self):
        self._lock = threading.Lock()
        self._load()
        self._last_api_time = 0
        self._dirty = False

    def _load(self):
        if DICT_PATH.exists():
            try:
                with open(DICT_PATH, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
                logger.info(f"Loaded {len(self._entries)} dictionary entries")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse dictionary: {e}")
                self._entries = {}
        else:
            logger.warning(f"Dictionary file not found: {DICT_PATH}")
            self._entries = {}

    def _save(self):
        if not self._dirty:
            return
        with self._lock:
            if not self._dirty:
                return
            try:
                with open(DICT_PATH, "w", encoding="utf-8") as f:
                    json.dump(self._entries, f, ensure_ascii=False, indent=2)
                self._dirty = False
                logger.debug(f"Saved {len(self._entries)} dictionary entries")
            except Exception as e:
                logger.error(f"Failed to save dictionary: {e}")

    def save(self):
        self._save()

    def lookup(self, word: str) -> dict | None:
        with self._lock:
            return self._entries.get(word)

    def _lookup_api(self, word: str, api_url: str = "") -> dict | None:
        if not api_url:
            return None

        resolved_ip, error = validate_dict_api_url(api_url)
        if error:
            logger.warning(f"Blocked dictionary API request: {error}")
            return None

        # Use resolved IP to prevent DNS rebinding (TOCTOU)
        request_url, original_host = build_url_with_ip(api_url, resolved_ip)

        with self._lock:
            if word in self._entries:
                return self._entries[word]

        elapsed = time.time() - self._last_api_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)

        data = urllib.parse.urlencode({"str": word}).encode()
        req = urllib.request.Request(request_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("accept", "*/*")
        req.add_header("Host", original_host)

        try:
            with self._lock:
                self._last_api_time = time.time()
            # Create SSL context that allows weak certificates
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=5, context=ssl_ctx)
            result = json.loads(resp.read().decode("utf-8"))
            if "1" in result and "list" in result["1"]:
                items = result["1"]["list"]
                if items:
                    item = items[0]
                    explain = item.get("explain", "")

                    word_class = "未知"
                    for abbr, cn in CLASS_MAP.items():
                        if abbr in explain:
                            word_class = cn
                            break

                    definition = re.sub(r'\([ก-ฮ]+\.\)', '', explain).strip()
                    definition = re.sub(r'\([^)]*\)', '', definition).strip()
                    if not definition:
                        definition = explain

                    entry = {
                        "chinese": definition,
                        "word_class": word_class,
                        "examples": [],
                        "compounds": [],
                        "usage": ""
                    }

                    with self._lock:
                        self._entries[word] = entry
                        self._dirty = True
                    logger.info(f"Dictionary API lookup: {word} -> {definition[:30]}...")
                    return entry
        except Exception as e:
            logger.warning(f"Dictionary API error for '{word}': {e}")

        return None

    def lookup_raw_api(self, word: str, api_url: str = "") -> dict | None:
        """Call dictionary API and return the raw response."""
        if not api_url:
            return None

        resolved_ip, error = validate_dict_api_url(api_url)
        if error:
            return None

        request_url, original_host = build_url_with_ip(api_url, resolved_ip)

        elapsed = time.time() - self._last_api_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)

        data = urllib.parse.urlencode({"str": word}).encode()
        req = urllib.request.Request(request_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("accept", "*/*")
        req.add_header("Host", original_host)

        try:
            with self._lock:
                self._last_api_time = time.time()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=5, context=ssl_ctx)
            return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Dictionary raw API error for '{word}': {e}")
            return None

    def get_definition(self, word: str, api_url: str = "") -> str:
        entry = self.lookup(word)
        if entry:
            return entry["chinese"]
        api_entry = self._lookup_api(word, api_url)
        if api_entry:
            return api_entry["chinese"]
        return f"[未收录：{word}]"

    def get_full_entry(self, word: str, api_url: str = "") -> dict:
        entry = self.lookup(word)
        if entry:
            return entry
        api_entry = self._lookup_api(word, api_url)
        if api_entry:
            return api_entry
        return {
            "chinese": f"[未收录：{word}]",
            "word_class": "未知",
            "examples": [],
            "compounds": [],
            "usage": ""
        }


dictionary = Dictionary()
