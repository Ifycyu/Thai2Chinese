"""Learning analysis service - core functions only."""
import os
import json
import logging
import httpx

from app.utils.url_validator import validate_url

logger = logging.getLogger(__name__)


async def do_learn(sentence: str, endpoint: str, token: str, model: str) -> str:
    """Call LLM API with Thai learning prompt."""
    if not endpoint or not token:
        return "请先在设置页面配置翻译API"

    _, error = validate_url(endpoint)
    if error:
        return f"翻译API地址被拒绝: {error}"

    request_url = endpoint

    prompt = f"""你是一个泰语老师，专门教中国学生学泰语。学生是泰语小白，零基础。

请分析以下泰语句子，只输出以下4点，用中文回答：

【句子】{sentence}

---

## 1. 翻译
给出完整的中文翻译。

## 2. 词汇
列出句子中的每个单词/短语，标注：
- 泰语原文
- 发音（用中文近似音标注）
- 中文意思

用表格形式展示。

## 3. 语法
说明句子的语法结构，指出：
- 句子类型（陈述句/疑问句/祈使句等）
- 语序特点
- 重要的语法点（如助词、时态标记等）

## 4. 需要注意的点
指出学习这个句子时需要注意的地方：
- 发音难点
- 常见错误
- 使用场景
- 文化注意事项

---

请用简洁明了的语言，适合零基础学生理解。"""

    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": token,
        "anthropic-version": "2023-06-01",
    }

    try:
        async with httpx.AsyncClient(timeout=60, verify=False) as client:
            resp = await client.post(request_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Learning analysis failed: {e}")
        return "分析失败，请稍后再试"
