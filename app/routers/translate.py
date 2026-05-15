"""Translation API proxy."""
import os
import urllib.request
import json
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["translate"])

DEFAULT_MODEL = "mimo-v2.5-pro"


class TranslateRequest(BaseModel):
    text: str


class TranslateResponse(BaseModel):
    original: str
    translated: str


def do_translate(text: str, endpoint: str, token: str, model: str) -> str:
    """Core translation function."""
    if not endpoint or not token:
        return "请先在设置页面配置翻译API"

    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": f"请将以下泰语翻译成中文，只输出翻译结果，不要解释：\n\n{text}"
        }]
    }).encode()

    request = urllib.request.Request(endpoint, data=payload, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("x-api-key", token)
    request.add_header("anthropic-version", "2023-06-01")

    try:
        resp = urllib.request.urlopen(request, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"].strip()
    except Exception as e:
        return f"翻译失败: {str(e)}"


@router.post("/translate", response_model=TranslateResponse)
async def translate(
    req: TranslateRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Translate Thai text to Chinese using LLM API."""
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", DEFAULT_MODEL)

    result = do_translate(req.text, endpoint, token, model)
    return TranslateResponse(original=req.text, translated=result)
