"""
词汇 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..database import save_vocab, get_vocab, check_vocab, list_vocab, update_vocab, delete_vocab

router = APIRouter(prefix="/admin/api", tags=["vocabulary"])


class VocabCreate(BaseModel):
    word: str
    familiarity: Optional[str] = "unknown"
    notes: Optional[str] = None
    experience_ids: Optional[list] = []


class VocabUpdate(BaseModel):
    word: Optional[str] = None
    familiarity: Optional[str] = None
    notes: Optional[str] = None
    experience_ids: Optional[list] = None


# ===== Vocabularies API =====

@router.get("/vocabularies")
async def api_list_vocab(
    familiarity: Optional[str] = Query(None, description="按熟悉度筛选")
):
    """获取词汇列表"""
    vocabularies = await list_vocab(familiarity=familiarity)
    return {"vocabularies": vocabularies}


@router.post("/vocabularies")
async def api_create_vocab(data: VocabCreate):
    """创建新词汇"""
    # 检查是否已存在
    existing = await check_vocab(data.word)
    if existing:
        raise HTTPException(status_code=409, detail=f"Word '{data.word}' already exists")

    vocab = await save_vocab(
        word=data.word,
        familiarity=data.familiarity,
        notes=data.notes,
        experience_ids=data.experience_ids
    )
    return {"success": True, "vocabulary": vocab}


@router.get("/vocabularies/{vocab_id}")
async def api_get_vocab(vocab_id: str):
    """获取单个词汇详情（包含关联的经历）"""
    vocab = await get_vocab(vocab_id)
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return vocab


@router.put("/vocabularies/{vocab_id}")
async def api_update_vocab(vocab_id: str, data: VocabUpdate):
    """更新词汇"""
    vocab = await update_vocab(
        vocab_id=vocab_id,
        word=data.word,
        familiarity=data.familiarity,
        notes=data.notes,
        experience_ids=data.experience_ids
    )
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return {"success": True, "vocabulary": vocab}


@router.delete("/vocabularies/{vocab_id}")
async def api_delete_vocab(vocab_id: str):
    """删除词汇"""
    success = await delete_vocab(vocab_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return {"success": True}
