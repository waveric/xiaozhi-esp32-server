"""
经历 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..database import save_experience, get_experience, search_experiences, list_experiences, update_experience, delete_experience

router = APIRouter(prefix="/admin/api", tags=["experiences"])


class ExperienceCreate(BaseModel):
    description: str
    search_tags: Optional[list] = []
    event_date: Optional[str] = None


class ExperienceUpdate(BaseModel):
    description: Optional[str] = None
    search_tags: Optional[list] = None
    event_date: Optional[str] = None


# ===== Experiences API =====

@router.get("/experiences")
async def api_list_experiences(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔")
):
    """获取经历列表，支持关键词和标签搜索"""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    experiences = await search_experiences(keyword=keyword, tags=tag_list)
    return {"experiences": experiences}


@router.post("/experiences")
async def api_create_experience(data: ExperienceCreate):
    """创建新经历"""
    exp = await save_experience(
        description=data.description,
        search_tags=data.search_tags,
        event_date=data.event_date
    )
    return {"success": True, "experience": exp}


@router.get("/experiences/{exp_id}")
async def api_get_experience(exp_id: str):
    """获取单个经历详情"""
    exp = await get_experience(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    return exp


@router.put("/experiences/{exp_id}")
async def api_update_experience(exp_id: str, data: ExperienceUpdate):
    """更新经历"""
    exp = await update_experience(
        exp_id=exp_id,
        description=data.description,
        search_tags=data.search_tags,
        event_date=data.event_date
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    return {"success": True, "experience": exp}


@router.delete("/experiences/{exp_id}")
async def api_delete_experience(exp_id: str):
    """删除经历"""
    success = await delete_experience(exp_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experience not found")
    return {"success": True}
