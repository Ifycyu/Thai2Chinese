"""Async task system for long-running API operations."""
import uuid
import asyncio
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from app.routers.translate import do_translate
from app.routers.learn import do_learn

router = APIRouter(tags=["async-tasks"])

# Task storage
tasks = {}


class TaskResponse(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    result: Optional[str] = None
    error: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str


class LearnRequest(BaseModel):
    sentence: str


async def run_translate_task(task_id: str, text: str, endpoint: str, token: str, model: str):
    """Run translation in background."""
    try:
        tasks[task_id]["status"] = "processing"
        result = await asyncio.to_thread(do_translate, text, endpoint, token, model)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


async def run_learn_task(task_id: str, sentence: str, endpoint: str, token: str, model: str):
    """Run learning analysis in background."""
    try:
        tasks[task_id]["status"] = "processing"
        result = await asyncio.to_thread(do_learn, sentence, endpoint, token, model)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


@router.post("/async/translate", response_model=TaskResponse)
async def async_translate(
    req: TranslateRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Start async translation task."""
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")

    if not endpoint or not token:
        return TaskResponse(task_id="", status="failed", error="请先配置翻译API")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "error": None}

    asyncio.create_task(run_translate_task(task_id, req.text, endpoint, token, model))

    return TaskResponse(task_id=task_id, status="pending")


@router.post("/async/learn", response_model=TaskResponse)
async def async_learn(
    req: LearnRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Start async learning analysis task."""
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")

    if not endpoint or not token:
        return TaskResponse(task_id="", status="failed", error="请先配置翻译API")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "error": None}

    asyncio.create_task(run_learn_task(task_id, req.sentence, endpoint, token, model))

    return TaskResponse(task_id=task_id, status="pending")


@router.get("/async/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get task status and result."""
    if task_id not in tasks:
        return TaskResponse(task_id=task_id, status="failed", error="任务不存在")

    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"],
        error=task["error"]
    )
