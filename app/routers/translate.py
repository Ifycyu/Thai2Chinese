"""Translation service - core functions only."""
import os
import json
import logging
import httpx

from app.utils.url_validator import validate_url

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "mimo-v2.5-pro"


async def do_translate(text: str, endpoint: str, token: str, model: str) -> str:
    """Async translation function using httpx."""
    if not endpoint or not token:
        return "请先在设置页面配置翻译API"

    _, error = validate_url(endpoint)
    if error:
        return f"翻译API地址被拒绝: {error}"

    request_url = endpoint

    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": f"请将以下泰语翻译成中文，只输出翻译结果，不要解释：\n\n{text}"
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": token,
        "anthropic-version": "2023-06-01",
    }

    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            resp = await client.post(request_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return "翻译失败，请稍后再试"
