"""
会话记录 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..database import save_session, save_session_message, get_session, list_sessions, delete_session

router = APIRouter(prefix="/admin/api", tags=["sessions"])


class SessionCreate(BaseModel):
    title: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str
    tool_call: Optional[str] = None


# ===== Sessions API =====

@router.get("/sessions")
async def api_list_sessions():
    """获取会话列表"""
    sessions = await list_sessions()
    return {"sessions": sessions}


@router.post("/sessions")
async def api_create_session(data: SessionCreate):
    """创建新会话"""
    session = await save_session(title=data.title)
    return {"success": True, "session": session}


@router.get("/sessions/{session_id}")
async def api_get_session(session_id: str):
    """获取会话详情（包含消息）"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/messages")
async def api_add_message(session_id: str, data: MessageCreate):
    """向会话添加消息"""
    # 先检查会话是否存在
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = await save_session_message(
        session_id=session_id,
        role=data.role,
        content=data.content,
        tool_call=data.tool_call
    )
    return {"success": True, "message": message}


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    """删除会话"""
    success = await delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}
