"""
角色管理 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import uuid

from ..database import (
    save_character, get_character, list_characters,
    update_character, delete_character, get_current_character,
    set_current_character
)
from ..config import BASE_DIR

router = APIRouter(prefix="/admin/api", tags=["characters"])


# ===== Pydantic Models =====

class CharacterCreate(BaseModel):
    name: str
    voice: str
    system_prompt: Optional[str] = ""
    description: Optional[str] = ""
    voice_source: Optional[str] = "builtin"


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    voice: Optional[str] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    voice_source: Optional[str] = None
    is_default: Optional[int] = None
    is_active: Optional[int] = None
    sort_order: Optional[int] = None


class SetCurrentCharacter(BaseModel):
    voice_id: str


# ===== Characters API =====

@router.get("/characters")
async def api_list_characters():
    """获取所有角色列表"""
    characters = await list_characters()
    return {"characters": characters}


@router.post("/characters")
async def api_create_character(data: CharacterCreate):
    """创建新角色"""
    character_data = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "voice": data.voice,
        "system_prompt": data.system_prompt or "",
        "description": data.description or "",
        "voice_source": data.voice_source or "builtin",
        "is_default": 0,
        "is_active": 1,
        "sort_order": 0,
    }
    character = await save_character(character_data)
    return {"success": True, "character": character}


@router.get("/characters/{character_id}")
async def api_get_character(character_id: str):
    """获取单个角色详情"""
    character = await get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/characters/{character_id}")
async def api_update_character(character_id: str, data: CharacterUpdate):
    """更新角色（支持部分更新）"""
    # 构建更新数据，排除 None 值
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    character = await update_character(character_id, update_data)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"success": True, "character": character}


@router.delete("/characters/{character_id}")
async def api_delete_character(character_id: str):
    """删除角色"""
    success = await delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"success": True}


@router.post("/characters/{character_id}/audio")
async def api_upload_character_audio(character_id: str, file: UploadFile = File(...)):
    """上传自定义音色参考音频"""
    # 验证角色存在
    character = await get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # 创建存储目录
    voices_dir = os.path.join(BASE_DIR, "data", "voices", character_id)
    os.makedirs(voices_dir, exist_ok=True)

    # 保存音频文件
    audio_path = os.path.join(voices_dir, "reference.wav")
    content = await file.read()
    with open(audio_path, "wb") as f:
        f.write(content)

    # 更新角色的 reference_audio 字段
    await update_character(character_id, {
        "reference_audio": f"data/voices/{character_id}/reference.wav",
        "voice_source": "custom"
    })

    return {
        "success": True,
        "path": f"data/voices/{character_id}/reference.wav"
    }


# ===== Current Character API =====

@router.get("/character/current")
async def api_get_current_character():
    """获取当前角色"""
    character = await get_current_character()
    if not character:
        return {"character": None}
    return {"character": character}


@router.post("/character/current")
async def api_set_current_character(data: SetCurrentCharacter):
    """设置当前角色"""
    success = await set_current_character(data.voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"success": True}
