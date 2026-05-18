"""Async task system with concurrency control and task expiration."""
import uuid
import asyncio
import time
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from app.routers.translate import do_translate
from app.routers.learn import do_learn

router = APIRouter(tags=["tasks"])

# ========== Configuration ==========
MAX_CONCURRENT_TRANSLATE = 5      # 最多同时5个翻译请求
MAX_CONCURRENT_LEARN = 3          # 最多同时3个学习请求
TASK_EXPIRE_SECONDS = 300         # 任务5分钟后过期
TASK_CLEANUP_INTERVAL = 60        # 每60秒清理一次过期任务

# ========== Semaphores ==========
translate_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSLATE)
learn_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LEARN)

# ========== Task Storage ==========
tasks = {}


class TaskResponse(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    result: Optional[str] = None
    error: Optional[str] = None
    queue_position: Optional[int] = None


class TranslateRequest(BaseModel):
    text: str


class LearnRequest(BaseModel):
    sentence: str


async def run_translate_task(task_id: str, text: str, endpoint: str, token: str, model: str):
    """Run translation with concurrency control."""
    async with translate_semaphore:
        try:
            tasks[task_id]["status"] = "processing"
            result = await asyncio.to_thread(do_translate, text, endpoint, token, model)
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
        finally:
            tasks[task_id]["completed_at"] = time.time()


async def run_learn_task(task_id: str, sentence: str, endpoint: str, token: str, model: str):
    """Run learning analysis with concurrency control."""
    async with learn_semaphore:
        try:
            tasks[task_id]["status"] = "processing"
            result = await asyncio.to_thread(do_learn, sentence, endpoint, token, model)
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
        finally:
            tasks[task_id]["completed_at"] = time.time()


def get_queue_position(task_type: str) -> int:
    """Get number of pending tasks in queue."""
    if task_type == "translate":
        return sum(1 for t in tasks.values() if t.get("type") == "translate" and t["status"] == "pending")
    return sum(1 for t in tasks.values() if t.get("type") == "learn" and t["status"] == "pending")


async def cleanup_expired_tasks():
    """Periodically clean up expired tasks."""
    while True:
        await asyncio.sleep(TASK_CLEANUP_INTERVAL)
        now = time.time()
        expired = [
            tid for tid, task in tasks.items()
            if task.get("completed_at") and (now - task["completed_at"]) > TASK_EXPIRE_SECONDS
        ]
        for tid in expired:
            del tasks[tid]


@router.post("/translate", response_model=TaskResponse)
async def translate(
    req: TranslateRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Start translation task with concurrency control."""
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")

    if not endpoint or not token:
        return TaskResponse(task_id="", status="failed", error="请先配置翻译API")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "type": "translate",
        "result": None,
        "error": None,
        "created_at": time.time(),
        "completed_at": None,
    }

    asyncio.create_task(run_translate_task(task_id, req.text, endpoint, token, model))

    queue_pos = get_queue_position("translate")
    return TaskResponse(task_id=task_id, status="pending", queue_position=queue_pos)


@router.post("/learn", response_model=TaskResponse)
async def learn(
    req: LearnRequest,
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    """Start learning analysis task with concurrency control."""
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")

    if not endpoint or not token:
        return TaskResponse(task_id="", status="failed", error="请先配置翻译API")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "type": "learn",
        "result": None,
        "error": None,
        "created_at": time.time(),
        "completed_at": None,
    }

    asyncio.create_task(run_learn_task(task_id, req.sentence, endpoint, token, model))

    queue_pos = get_queue_position("learn")
    return TaskResponse(task_id=task_id, status="pending", queue_position=queue_pos)


@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get task status and result."""
    if task_id not in tasks:
        return TaskResponse(task_id=task_id, status="failed", error="任务不存在或已过期")

    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"],
        error=task["error"]
    )
