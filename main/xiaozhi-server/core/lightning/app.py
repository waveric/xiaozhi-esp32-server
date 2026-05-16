"""
Lightning Tools FastAPI 应用（xiaozhi-esp32-server 集成版）
提供 Web 管理界面和 API 端点
"""
import os
import asyncio
import yaml
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .database import init_db, get_memory, get_role_prompt, get_shared_memory
from .config import AGENT_BASE_PROMPT_PATH
from .auth import AuthManager, LoginRequest, LoginResponse, create_login_response, clear_auth_cookie
from .takeover import TakeoverManager
from .config_manager import ConfigManager

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


def create_app(chat_monitor=None) -> FastAPI:
    """创建 FastAPI 应用实例

    Args:
        chat_monitor: ChatMonitor 实例，用于 WebSocket 实时消息推送
    """
    app = FastAPI(title="Lightning Tools", lifespan=lifespan)

    # 存储 chat_monitor 到 app.state
    app.state.chat_monitor = chat_monitor

    # 创建 TakeoverManager 实例
    takeover_manager = TakeoverManager(chat_monitor)

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

    # ===== TakeoverManager API 路由 =====

    @app.post("/admin/api/takeover/{session_id}/enable")
    async def takeover_enable(session_id: str):
        """开启接管模式"""
        result = takeover_manager.enable(session_id)
        return result

    @app.post("/admin/api/takeover/{session_id}/disable")
    async def takeover_disable(session_id: str):
        """关闭接管模式"""
        result = takeover_manager.disable(session_id)
        return result

    @app.get("/admin/api/takeover/{session_id}/status")
    async def takeover_status(session_id: str):
        """获取接管状态"""
        return {"active": takeover_manager.is_active(session_id)}

    @app.post("/admin/api/takeover/{session_id}/respond")
    async def takeover_respond(session_id: str, body: dict):
        """以接管身份回复消息"""
        text = body.get("text", "")
        result = takeover_manager.respond(session_id, text)
        return result

    @app.post("/admin/api/takeover/{session_id}/execute-tool")
    async def takeover_execute_tool(session_id: str, body: dict):
        """执行工具"""
        tool_name = body.get("tool_name")
        arguments = body.get("arguments", {})
        result = await takeover_manager.execute_tool(session_id, tool_name, arguments)
        return result

    @app.get("/admin/api/takeover/{session_id}/tools")
    async def takeover_tools(session_id: str):
        """获取可用工具列表"""
        return takeover_manager.get_tools()

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

    # ===== 配置管理 API 路由 =====

    # 创建 ConfigManager 实例
    config_manager = ConfigManager()

    @app.get("/admin/api/config")
    async def get_config():
        """获取当前激活的配置"""
        try:
            config = config_manager.get_merged_config()
            return {"success": True, "config": config}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/admin/api/config/list")
    async def list_configs():
        """列出所有可用配置文件"""
        try:
            configs = config_manager.list_configs()
            return {"success": True, "configs": configs}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/admin/api/config/{filename}")
    async def get_config_file(filename: str):
        """获取指定配置文件内容"""
        try:
            if filename == "config.yaml":
                config = config_manager.get_default_config()
            else:
                config = config_manager.load_config(filename)
            return {"success": True, "config": config, "filename": filename}
        except FileNotFoundError:
            return {"success": False, "error": f"配置文件不存在: {filename}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.post("/admin/api/config/save")
    async def save_config(body: dict):
        """保存配置到指定文件"""
        filename = body.get("filename")
        config = body.get("config")
        if not filename or not config:
            return {"success": False, "error": "缺少 filename 或 config 参数"}
        return config_manager.save_config(filename, config)

    @app.post("/admin/api/config/switch")
    async def switch_config(body: dict):
        """切换配置文件"""
        filename = body.get("filename")
        if not filename:
            return {"success": False, "error": "缺少 filename 参数"}
        return config_manager.switch_config(filename)

    @app.post("/admin/api/config/reset")
    async def reset_config():
        """重置为默认配置"""
        return config_manager.reset_to_default()

    @app.delete("/admin/api/config/{filename}")
    async def delete_config(filename: str):
        """删除指定配置文件"""
        return config_manager.delete_config(filename)

    @app.post("/admin/api/config/restart")
    async def restart_service(body: dict = None):
        """重启服务"""
        config_file = body.get("config_file") if body else None
        return config_manager.restart(config_file)

    @app.get("/admin/api/config/restart-log")
    async def get_restart_log():
        """获取重启日志"""
        return {"log": config_manager.get_restart_log()}

    @app.get("/admin/api/config/restart-result")
    async def get_restart_result():
        """获取最近一次重启结果"""
        return config_manager.get_restart_result()

    @app.post("/admin/api/config/update")
    async def update_config(body: dict):
        """更新当前激活配置的特定字段"""
        return config_manager.update_active_config(body)

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

    @app.get("/admin/chat-monitor")
    async def admin_chat_monitor(request: Request, _: Optional[str] = Depends(auth_dependency)):
        """聊天监控页面"""
        return templates.TemplateResponse(request, "chat_monitor.html")

    # ===== WebSocket 端点 =====

    @app.websocket("/admin/ws/chat")
    async def websocket_chat(websocket: WebSocket, session_id: str = None):
        """WebSocket 端点，实时推送对话消息

        Args:
            websocket: WebSocket 连接
            session_id: 可选的会话 ID，用于订阅特定会话的消息

        消息格式:
            {"type": "user_message", "content": "...", "is_history": false}
            {"type": "llm_text", "content": "...", "is_history": false}
            {"type": "llm_reply", "content": "...", "is_history": false}
            {"type": "tool_call", "content": {...}, "is_history": false}
            {"type": "tool_result", "content": {...}, "is_history": false}
        """
        await websocket.accept()

        # 获取 ChatMonitor 实例
        chat_monitor = websocket.app.state.chat_monitor

        if chat_monitor is None:
            # ChatMonitor 未配置，发送错误并关闭
            await websocket.send_json({"type": "error", "content": "ChatMonitor not configured"})
            await websocket.close()
            return

        # 如果没有 session_id，尝试获取当前活跃的 session
        if not session_id:
            # 获取第一个有 handler 的 session
            if chat_monitor.handlers:
                session_id = next(iter(chat_monitor.handlers.keys()))
            else:
                session_id = "default"

        try:
            # 发送历史消息（如果有 handler 且有 dialogue）
            handler = chat_monitor.get_handler(session_id)
            if handler and hasattr(handler, 'dialogue'):
                for msg in handler.dialogue.dialogue:
                    # 跳过系统消息和临时消息
                    if msg.role == "system" or msg.is_temporary:
                        continue

                    # 构建历史消息
                    if msg.role == "user":
                        await websocket.send_json({
                            "type": "user_message",
                            "content": msg.content,
                            "is_history": True
                        })
                    elif msg.role == "assistant":
                        if msg.tool_calls:
                            # 工具调用消息
                            await websocket.send_json({
                                "type": "tool_call",
                                "content": msg.tool_calls,
                                "is_history": True
                            })
                        else:
                            # 助手文本消息
                            await websocket.send_json({
                                "type": "llm_reply",
                                "content": msg.content,
                                "is_history": True
                            })
                    elif msg.role == "tool":
                        # 工具结果消息
                        await websocket.send_json({
                            "type": "tool_result",
                            "content": {
                                "tool_call_id": msg.tool_call_id,
                                "content": msg.content
                            },
                            "is_history": True
                        })

            # 订阅实时消息流
            async for msg in chat_monitor.subscribe(session_id):
                # 添加 is_history 标记（实时消息都是 false）
                msg["is_history"] = False
                await websocket.send_json(msg)

        except WebSocketDisconnect:
            pass
        finally:
            # ChatMonitor.subscribe() 的 finally 会自动调用 unsubscribe
            pass

    return app
