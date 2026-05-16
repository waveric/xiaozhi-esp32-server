"""
TakeoverManager 接管管理器

允许家长/管理员通过 Web UI 接管对话，
跳过 LLM 处理，直接以指定文字回复设备端（TTS 播放）。

核心方法：
- enable(session_id):  开启接管模式
- disable(session_id): 关闭接管模式
- is_active(session_id): 检查是否处于接管模式
- respond(session_id, text): 以接管身份回复消息
"""

import uuid
from typing import Set

from core.providers.tts.dto.dto import TTSMessageDTO, ContentType, SentenceType
from core.utils.dialogue import Message
from core.lightning.chat_monitor import ChatMonitor


class TakeoverManager:
    """接管管理器

    当接管模式开启时，chat() 方法中的 if-check 会跳过 LLM 调用，
    家长可通过 respond() 直接将文字推送给设备端（写入对话历史 + TTS 播放）。
    """

    def __init__(self, chat_monitor: ChatMonitor):
        """
        Args:
            chat_monitor: ChatMonitor 实例，用于获取 handler 引用和推送消息
        """
        self.chat_monitor = chat_monitor
        self.active_sessions: Set[str] = set()

    def enable(self, session_id: str) -> dict:
        """开启接管模式

        Args:
            session_id: 会话 ID

        Returns:
            dict: {"success": True, "session_id": session_id}
        """
        self.active_sessions.add(session_id)
        return {"success": True, "session_id": session_id}

    def disable(self, session_id: str) -> dict:
        """关闭接管模式

        Args:
            session_id: 会话 ID

        Returns:
            dict: {"success": True, "session_id": session_id}
        """
        self.active_sessions.discard(session_id)
        return {"success": True, "session_id": session_id}

    def is_active(self, session_id: str) -> bool:
        """检查是否处于接管模式

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否处于接管模式
        """
        return session_id in self.active_sessions

    def respond(self, session_id: str, text: str) -> dict:
        """以接管身份回复消息

        将文字写入对话历史并触发 TTS 播放，同时推送给 ChatMonitor 订阅者。

        Args:
            session_id: 会话 ID
            text: 回复文本

        Returns:
            dict: {"success": True} 或 {"success": False, "error": "..."}
        """
        if not self.chat_monitor:
            return {"success": False, "error": "ChatMonitor not configured"}

        handler = self.chat_monitor.get_handler(session_id)
        if not handler:
            return {"success": False, "error": "Session not found"}

        # 写入对话历史
        handler.dialogue.put(Message(role='assistant', content=text))

        # 触发 TTS 播放（标准三段式：FIRST → MIDDLE(TEXT) → LAST）
        sid = str(uuid.uuid4().hex)
        handler.tts.tts_text_queue.put(TTSMessageDTO(
            sentence_id=sid,
            sentence_type=SentenceType.FIRST,
            content_type=ContentType.ACTION,
        ))
        handler.tts.tts_text_queue.put(TTSMessageDTO(
            sentence_id=sid,
            sentence_type=SentenceType.MIDDLE,
            content_type=ContentType.TEXT,
            content_detail=text,
        ))
        handler.tts.tts_text_queue.put(TTSMessageDTO(
            sentence_id=sid,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        ))

        # 推送到 ChatMonitor 订阅者
        self.chat_monitor.on_message_sync(session_id, 'takeover_response', text)

        return {"success": True}

    async def execute_tool(self, session_id: str, tool_name: str, arguments: dict) -> dict:
        """执行工具

        在接管模式下，可以调用 lightning-tools 提供的工具函数。

        Args:
            session_id: 会话 ID
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            dict: {"success": True, "result": ...} 或 {"success": False, "error": "..."}
        """
        from .tools import (
            get_memory, update_memory,
            search_story, get_story_text, save_story, delete_story,
            check_vocabulary, update_vocabulary,
            save_experience, search_experiences,
            get_character_info, list_characters
        )

        # 工具映射表
        tool_map = {
            # Memory 工具
            "get_memory": get_memory,
            "update_memory": update_memory,
            # Story 工具
            "search_story": search_story,
            "get_story_text": get_story_text,
            "save_story": save_story,
            "delete_story": delete_story,
            # Vocabulary 工具
            "check_vocabulary": check_vocabulary,
            "update_vocabulary": update_vocabulary,
            # Experience 工具
            "save_experience": save_experience,
            "search_experiences": search_experiences,
            # Character 工具
            "get_character_info": get_character_info,
            "list_characters": list_characters,
        }

        if tool_name not in tool_map:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # 检查会话是否存在（可选，不强制）
        if self.chat_monitor:
            handler = self.chat_monitor.get_handler(session_id)
            # 即使没有活跃会话也允许执行工具（用于预览等场景）

        try:
            result = await tool_map[tool_name](**arguments)
            return {"success": True, "result": result}
        except TypeError as e:
            return {"success": False, "error": f"Invalid arguments: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tools(self) -> list:
        """获取可用工具列表

        Returns:
            list: 工具定义列表，每个工具包含 name, description, parameters
        """
        return [
            {
                "name": "get_memory",
                "description": "获取长期记忆内容，包含关于孩子的重要信息",
                "parameters": {}
            },
            {
                "name": "update_memory",
                "description": "更新长期记忆内容",
                "parameters": {
                    "content": {"type": "string", "required": True, "description": "新的记忆内容"}
                }
            },
            {
                "name": "search_story",
                "description": "搜索故事库中的故事",
                "parameters": {
                    "keyword": {"type": "string", "required": True, "description": "搜索关键词"},
                    "limit": {"type": "integer", "required": False, "description": "返回结果数量限制，默认5"}
                }
            },
            {
                "name": "get_story_text",
                "description": "获取故事的完整文本内容",
                "parameters": {
                    "story_id": {"type": "string", "required": True, "description": "故事ID"}
                }
            },
            {
                "name": "save_story",
                "description": "保存新故事到故事库",
                "parameters": {
                    "title": {"type": "string", "required": True, "description": "故事标题"},
                    "content": {"type": "string", "required": True, "description": "故事内容"},
                    "tags": {"type": "array", "required": False, "description": "标签列表"}
                }
            },
            {
                "name": "delete_story",
                "description": "删除故事",
                "parameters": {
                    "story_id": {"type": "string", "required": True, "description": "要删除的故事ID"}
                }
            },
            {
                "name": "check_vocabulary",
                "description": "检查词汇的熟悉度和关联经历",
                "parameters": {
                    "word": {"type": "string", "required": True, "description": "要检查的词汇"}
                }
            },
            {
                "name": "update_vocabulary",
                "description": "更新词汇信息",
                "parameters": {
                    "word": {"type": "string", "required": True, "description": "词汇"},
                    "familiarity": {"type": "string", "required": False, "description": "熟悉度 (unknown/vague/familiar)"},
                    "notes": {"type": "string", "required": False, "description": "备注"},
                    "experience_ids": {"type": "array", "required": False, "description": "关联的经历ID列表"}
                }
            },
            {
                "name": "save_experience",
                "description": "保存新的经历记录",
                "parameters": {
                    "description": {"type": "string", "required": True, "description": "事件描述"},
                    "search_tags": {"type": "string", "required": False, "description": "搜索标签（空格分隔）"},
                    "event_date": {"type": "string", "required": False, "description": "事件日期"}
                }
            },
            {
                "name": "search_experiences",
                "description": "搜索经历记录",
                "parameters": {
                    "keyword": {"type": "string", "required": False, "description": "搜索关键词"},
                    "limit": {"type": "integer", "required": False, "description": "返回结果数量限制，默认10"}
                }
            },
            {
                "name": "get_character_info",
                "description": "获取指定角色的详细信息",
                "parameters": {
                    "name": {"type": "string", "required": False, "description": "角色名称（支持模糊匹配）"},
                    "character_id": {"type": "string", "required": False, "description": "角色 ID（精确匹配）"}
                }
            },
            {
                "name": "list_characters",
                "description": "获取所有角色列表",
                "parameters": {}
            }
        ]
