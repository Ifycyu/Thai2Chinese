"""Thai learning API - calls LLM with learning-focused prompts."""
import os
import urllib.request
import json
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["learn"])


class LearnRequest(BaseModel):
    sentence: str


class LearnResponse(BaseModel):
    sentence: str
    explanation: str


def do_learn(sentence: str, endpoint: str, token: str, model: str) -> str:
    """Call LLM API with Thai learning prompt."""
    if not endpoint or not token:
        return "请先在设置页面配置翻译API"

    prompt = f"""你是一个泰语老师，专门教中国学生学泰语。学生是泰语小白，零基础。

请详细分析以下泰语句子，用中文回答：

【句子】{sentence}

请按以下格式输出：

1. 【整句翻译】
   - 给出完整的中文翻译

2. 【逐词解析】
   - 列出每个单词
   - 标注发音（用拼音或中文近似音）
   - 给出中文意思
   - 说明词性

3. 【声调说明】
   - 标注每个音节的声调
   - 用简单的语言解释声调规则

4. 【语法要点】
   - 说明句子结构
   - 指出重要的语法点

5. 【发音技巧】
   - 哪些音需要注意
   - 常见错误提醒

6. 【文化小知识】
   - 这个句子在什么场景使用
   - 有什么文化背景

7. 【类似表达】
   - 给出2-3个类似的常用句子
   - 附上中文翻译

请用通俗易懂的语言，让零基础的学生也能看懂。"""

    payload = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }).encode()

    request = urllib.request.Request(endpoint, data=payload, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("x-api-key", token)
    request.add_header("anthropic-version", "2023-06-01")

    try:
        resp = urllib.request.urlopen(request, timeout=60)
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"].strip()
    except Exception as e:
        return f"分析失败: {str(e)}"


@router.post("/learn", response_model=LearnResponse)
async def learn(
    req: LearnRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Analyze Thai sentence for learning."""
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")

    result = do_learn(req.sentence, endpoint, token, model)
    return LearnResponse(sentence=req.sentence, explanation=result)
