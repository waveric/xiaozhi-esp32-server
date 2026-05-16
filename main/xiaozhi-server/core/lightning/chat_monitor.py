"""
ChatMonitor 分发器类

用于在 chat() 的关键位置同步推送消息给 WebSocket 客户端，
支持多订阅者模式，为后续 TakeoverManager 提供基础。
"""

import asyncio
from typing import Dict, List, Any, AsyncIterator, Optional
from collections import defaultdict


class ChatMonitor:
    """聊天监控分发器

    功能：
    1. 在 chat() 关键位置推送消息给所有订阅者
    2. 支持同步和异步两种调用方式
    3. 管理 ConnectionHandler 引用，供 TakeoverManager 使用
    """

    def __init__(self):
        # session_id -> 订阅者队列列表
        self.subscriber_queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        # session_id -> ConnectionHandler 引用
        self.handlers: Dict[str, Any] = {}

    def register_handler(self, session_id: str, handler):
        """注册 ConnectionHandler 以便 TakeoverManager 使用

        Args:
            session_id: 会话 ID
            handler: ConnectionHandler 实例
        """
        self.handlers[session_id] = handler

    def unregister_handler(self, session_id: str):
        """注销 ConnectionHandler

        Args:
            session_id: 会话 ID
        """
        if session_id in self.handlers:
            del self.handlers[session_id]
        # 同时清理订阅者队列
        if session_id in self.subscriber_queues:
            self.subscriber_queues[session_id].clear()

    def get_handler(self, session_id: str) -> Optional[Any]:
        """获取 ConnectionHandler

        Args:
            session_id: 会话 ID

        Returns:
            ConnectionHandler 实例或 None
        """
        return self.handlers.get(session_id)

    async def on_message(self, session_id: str, msg_type: str, content: Any):
        """推送消息给所有订阅者（异步版本）

        Args:
            session_id: 会话 ID
            msg_type: 消息类型 (user_message, llm_text, tool_call, tool_result, llm_reply)
            content: 消息内容
        """
        for queue in self.subscriber_queues[session_id]:
            await queue.put({"type": msg_type, "content": content})

    def on_message_sync(self, session_id: str, msg_type: str, content: Any):
        """推送消息给所有订阅者（同步版本，用于从 ThreadPool 调用）

        Args:
            session_id: 会话 ID
            msg_type: 消息类型
            content: 消息内容
        """
        if not self.subscriber_queues[session_id]:
            return

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        for queue in self.subscriber_queues[session_id]:
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": msg_type, "content": content}),
                loop
            )

    async def subscribe(self, session_id: str) -> AsyncIterator[dict]:
        """订阅消息流

        Args:
            session_id: 会话 ID

        Yields:
            dict: 消息对象 {"type": msg_type, "content": content}
        """
        queue = asyncio.Queue()
        self.subscriber_queues[session_id].append(queue)
        try:
            while True:
                msg = await queue.get()
                yield msg
        finally:
            self.unsubscribe(session_id, queue)

    def unsubscribe(self, session_id: str, queue: asyncio.Queue):
        """取消订阅

        Args:
            session_id: 会话 ID
            queue: 订阅者队列
        """
        if queue in self.subscriber_queues[session_id]:
            self.subscriber_queues[session_id].remove(queue)

    def has_subscribers(self, session_id: str) -> bool:
        """检查是否有订阅者

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否有订阅者
        """
        return len(self.subscriber_queues[session_id]) > 0
