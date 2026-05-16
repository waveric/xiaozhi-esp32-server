"""
Lightning Tools FastAPI 应用（xiaozhi-esp32-server 集成版）
提供 Web 管理界面和 API 端点
"""
import os
import yaml
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .database import init_db, get_memory, get_role_prompt, get_shared_memory
from .config import AGENT_BASE_PROMPT_PATH
from .auth import AuthManager, LoginRequest, LoginResponse, create_login_response, clear_auth_cookie

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


def load_config() -> dict:
    """加载配置文件"""
    # 优先读取 data/.config.yaml，否则读取默认 config.yaml
    base_dir = Path(__file__).parent.parent.parent
    config_path = base_dir / "data" / ".config.yaml"
    if not config_path.exists():
        config_path = base_dir / "config.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(title="Lightning Tools", lifespan=lifespan)

    # 加载配置并创建认证管理器
    config = load_config()
    auth_manager = AuthManager(config)

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

    # ===== 认证 API 路由 =====

    @app.post("/admin/api/login")
    async def api_login(login_req: LoginRequest, response: Response):
        """登录 API"""
        result = auth_manager.login(login_req.username, login_req.password)
        return create_login_response(response, result)

    @app.post("/admin/api/logout")
    async def api_logout(request: Request, response: Response):
        """登出 API"""
        token = request.cookies.get("auth_token")
        if token:
            auth_manager.logout(token)
        clear_auth_cookie(response)
        return {"success": True, "message": "已登出"}

    @app.get("/admin/api/auth_status")
    async def auth_status(request: Request):
        """获取认证状态"""
        cookie_token = request.cookies.get("auth_token")
        is_authenticated = auth_manager.check_auth(cookie_token) if auth_manager.is_enabled() else True
        return {
            "enabled": auth_manager.is_enabled(),
            "authenticated": is_authenticated
        }

    # ===== 认证依赖 =====
    auth_dependency = auth_manager.get_auth_dependency()

    # ===== 页面路由 =====

    @app.get("/")
    async def root():
        """根路径重定向到管理页面"""
        return RedirectResponse(url="/admin/")

    # ===== 登录页面（认证启用时） =====

    @app.get("/admin/login")
    async def admin_login_page(request: Request):
        """登录页面"""
        if not auth_manager.is_enabled():
            # 认证未启用，直接跳转到管理页面
            return RedirectResponse(url="/admin/")

        # 检查是否已登录
        cookie_token = request.cookies.get("auth_token")
        if auth_manager.check_auth(cookie_token):
            return RedirectResponse(url="/admin/")

        return templates.TemplateResponse(request, "login.html", {
            "auth_enabled": True
        })

    # ===== 需要认证的管理页面 =====

    @app.get("/admin/")
    async def admin_memory(request: Request, _: Optional[str] = Depends(auth_dependency)):
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
    async def admin_stories(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """故事库页面"""
        return templates.TemplateResponse(request, "stories.html")

    @app.get("/admin/stories/new")
    async def admin_story_new(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """新建故事页面"""
        return templates.TemplateResponse(request, "story_edit.html", {"story": None})

    @app.get("/admin/stories/{story_id}")
    async def admin_story_edit(request: Request, story_id: str, _: Optional[str] = Depends(auth_dependency)):
        """编辑故事页面"""
        from .database import get_story
        story = await get_story(story_id)
        return templates.TemplateResponse(request, "story_edit.html", {"story": story})

    @app.get("/admin/vocabulary")
    async def admin_vocabulary(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """词汇管理页面"""
        return templates.TemplateResponse(request, "vocabulary.html")

    @app.get("/admin/experiences")
    async def admin_experiences(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """经历管理页面"""
        return templates.TemplateResponse(request, "experiences.html")

    @app.get("/admin/history")
    async def admin_history(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """会话记录页面"""
        return templates.TemplateResponse(request, "history.html")

    @app.get("/admin/characters")
    async def admin_characters(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """角色管理页面"""
        return templates.TemplateResponse(request, "characters.html")

    return app
