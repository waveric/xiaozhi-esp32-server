"""
Lightning Tools FastAPI 应用（xiaozhi-esp32-server 集成版）
提供 Web 管理界面和 API 端点
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .database import init_db, get_memory, get_role_prompt, get_shared_memory
from .config import AGENT_BASE_PROMPT_PATH

# 路径配置
LIGHTNING_DIR = Path(__file__).parent
TEMPLATE_DIR = LIGHTNING_DIR / "templates"
STATIC_DIR = LIGHTNING_DIR / "static"
DATA_DIR = LIGHTNING_DIR.parent.parent / "data"
AUDIO_DIR = DATA_DIR / "audio"

# Jinja2 模板
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def read_rules_content() -> str:
    """读取 agent-base-prompt.txt 的行为规则内容"""
    try:
        with open(AGENT_BASE_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "# 未找到 agent-base-prompt.txt 文件"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    print("[OK] Lightning 数据库初始化完成")
    yield


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(title="Lightning Tools", lifespan=lifespan)

    # 挂载静态文件
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # 挂载音频文件目录
    if AUDIO_DIR.exists():
        app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

    # ===== 注册 Web API 路由 =====
    from .web_api import memory, stories, vocabulary, experiences, rules, sessions, characters

    app.include_router(memory.router)
    app.include_router(stories.router)
    app.include_router(vocabulary.router)
    app.include_router(experiences.router)
    app.include_router(rules.router)
    app.include_router(sessions.router)
    app.include_router(characters.router)

    # ===== 页面路由 =====

    @app.get("/")
    async def root():
        """根路径重定向到管理页面"""
        return RedirectResponse(url="/admin/")

    @app.get("/admin/")
    async def admin_memory(request: Request):
        """提示词管理页面（角色设定 + 长期记忆 + 行为规则）"""
        role_prompt = await get_role_prompt()
        content = await get_memory()
        rules_content = read_rules_content()
        return templates.TemplateResponse(request, "memory.html", {
            "role_prompt": role_prompt,
            "content": content,
            "rules_content": rules_content,
        })

    @app.get("/admin/stories")
    async def admin_stories(request: Request):
        """故事库页面"""
        return templates.TemplateResponse(request, "stories.html")

    @app.get("/admin/stories/new")
    async def admin_story_new(request: Request):
        """新建故事页面"""
        return templates.TemplateResponse(request, "story_edit.html", {"story": None})

    @app.get("/admin/stories/{story_id}")
    async def admin_story_edit(request: Request, story_id: str):
        """编辑故事页面"""
        from .database import get_story
        story = await get_story(story_id)
        return templates.TemplateResponse(request, "story_edit.html", {"story": story})

    @app.get("/admin/vocabulary")
    async def admin_vocabulary(request: Request):
        """词汇管理页面"""
        return templates.TemplateResponse(request, "vocabulary.html")

    @app.get("/admin/experiences")
    async def admin_experiences(request: Request):
        """经历管理页面"""
        return templates.TemplateResponse(request, "experiences.html")

    @app.get("/admin/history")
    async def admin_history(request: Request):
        """会话记录页面"""
        return templates.TemplateResponse(request, "history.html")

    @app.get("/admin/characters")
    async def admin_characters(request: Request):
        """角色管理页面"""
        return templates.TemplateResponse(request, "characters.html")

    return app
