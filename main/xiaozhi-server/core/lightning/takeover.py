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
