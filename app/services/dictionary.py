import json
import os
import re
import time
import threading
import urllib.request
import urllib.parse
from pathlib import Path

CLASS_MAP = {
    "น.": "名词", "ก.": "动词", "ว.": "形容词", "สรร.": "代词",
    "วิ.": "副词", "สัน.": "连词", "อ.": "感叹词", "ล.": "量词",
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
            with open(DICT_PATH, "r", encoding="utf-8") as f:
                self._entries = json.load(f)
        else:
            self._entries = {}

    def _save(self):
        """Save entries to disk (only if changed, thread-safe)."""
        if not self._dirty:
            return
        with self._lock:
            if not self._dirty:
                return
            with open(DICT_PATH, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
            self._dirty = False

    def save(self):
        """Public method to force save."""
        self._save()

    def lookup(self, word: str) -> dict | None:
        """Thread-safe lookup."""
        with self._lock:
            return self._entries.get(word)

    def _lookup_api(self, word: str, api_url: str = "") -> dict | None:
        """Look up a word using the free API and cache to memory."""
        if not api_url:
            return None

        # Check memory cache first (thread-safe)
        with self._lock:
            if word in self._entries:
                return self._entries[word]

        # Rate limit: 0.1s between API calls (thread-safe)
        with self._lock:
            elapsed = time.time() - self._last_api_time
            if elapsed < 0.1:
                wait_time = 0.1 - elapsed
            else:
                wait_time = 0
        if wait_time > 0:
            time.sleep(wait_time)

        data = urllib.parse.urlencode({"str": word}).encode()
        req = urllib.request.Request(api_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("accept", "*/*")

        try:
            with self._lock:
                self._last_api_time = time.time()
            resp = urllib.request.urlopen(req, timeout=5)
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

                    # Cache to memory (thread-safe)
                    with self._lock:
                        self._entries[word] = entry
                        self._dirty = True
                    return entry
        except Exception:
            pass

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
