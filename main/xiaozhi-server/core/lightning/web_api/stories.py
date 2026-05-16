"""
故事库 API（xiaozhi-esp32-server 集成版）
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..database import save_story, get_story, search_stories, list_stories, update_story, delete_story

router = APIRouter(prefix="/admin/api", tags=["stories"])


class StoryCreate(BaseModel):
    title: str
    text: str
    tags: Optional[list] = []
    summary: Optional[str] = None


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    tags: Optional[list] = None
    summary: Optional[str] = None


# ===== Stories API =====

@router.get("/stories")
async def api_list_stories(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔")
):
    """获取故事列表，支持关键词和标签搜索"""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    stories = await search_stories(keyword=keyword, tags=tag_list)
    return {"stories": stories}


@router.post("/stories")
async def api_create_story(data: StoryCreate):
    """创建新故事"""
    story = await save_story(
        title=data.title,
        text=data.text,
        tags=data.tags,
        summary=data.summary
    )
    return {"success": True, "story": story}


@router.get("/stories/{story_id}")
async def api_get_story(story_id: str):
    """获取单个故事详情"""
    story = await get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.put("/stories/{story_id}")
async def api_update_story(story_id: str, data: StoryUpdate):
    """更新故事"""
    story = await update_story(
        story_id=story_id,
        title=data.title,
        text=data.text,
        tags=data.tags,
        summary=data.summary
    )
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"success": True, "story": story}


@router.delete("/stories/{story_id}")
async def api_delete_story(story_id: str):
    """删除故事"""
    success = await delete_story(story_id)
    if not success:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"success": True}
