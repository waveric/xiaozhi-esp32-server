"""
记忆与角色设定 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_memory, set_memory, get_role_prompt, set_role_prompt

router = APIRouter(prefix="/admin/api", tags=["memory"])


class MemoryUpdate(BaseModel):
    content: str


class RolePromptUpdate(BaseModel):
    content: str


# ===== Memory API =====

@router.get("/memory")
async def api_get_memory():
    """获取记忆内容"""
    content = await get_memory()
    return {"content": content}


@router.put("/memory")
async def api_set_memory(data: MemoryUpdate):
    """更新记忆内容"""
    await set_memory(data.content)
    return {"success": True, "content": data.content}


# ===== Role Prompt API =====

@router.get("/role_prompt")
async def api_get_role_prompt():
    """获取角色设定"""
    content = await get_role_prompt()
    return {"content": content}


@router.put("/role_prompt")
async def api_set_role_prompt(data: RolePromptUpdate):
    """更新角色设定"""
    await set_role_prompt(data.content)
    return {"success": True, "content": data.content}


# ===== Context Provider API (for xiaozhi-esp32-server) =====

@router.get("/context")
async def api_get_context(request: Request):
    """获取上下文数据，供 xiaozhi-esp32-server 的 context_providers 使用

    返回格式符合 xiaozhi-esp32-server 的规范：
    {
        "code": 0,
        "msg": "success",
        "data": {
            "长期记忆": "...",
            "角色设定": "..."
        }
    }
    """
    device_id = request.headers.get("device-id", "unknown")

    # 获取记忆和角色设定
    memory = await get_memory()
    role_prompt = await get_role_prompt()

    # 构建返回数据
    data = {}
    if memory and memory.strip():
        data["长期记忆"] = memory
    if role_prompt and role_prompt.strip():
        data["角色设定"] = role_prompt

    return {
        "code": 0,
        "msg": "success",
        "data": data
    }
