"""
Lightning Tools Memory Provider
从本地 lightning 数据库获取长期记忆和角色设定
"""
import asyncio
from ..base import MemoryProviderBase, logger
from core.lightning.database import (
    get_shared_memory,
    get_memory,
    get_role_prompt,
    get_current_character,
)

TAG = __name__


class MemoryProvider(MemoryProviderBase):
    """从本地 lightning 数据库获取记忆的 Memory Provider"""

    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        self.memory_content = ""
        self.role_prompt = ""
        self._cached_memory = None  # 缓存格式化后的记忆

    def init_memory(self, role_id, llm, summary_memory=None, **kwargs):
        """初始化记忆 - 从本地 lightning 数据库获取记忆和角色设定"""
        super().init_memory(role_id, llm, **kwargs)

        # 从本地数据库获取记忆（同步包装异步调用）
        try:
            # 尝试获取共享记忆和当前角色设定
            memory_content = self._run_async(get_shared_memory())
            character = self._run_async(get_current_character())

            # 如果角色存在，使用角色的 system_prompt
            if character and character.get("system_prompt"):
                self.role_prompt = character["system_prompt"]
            else:
                # fallback 到旧的 role_prompt 表
                self.role_prompt = self._run_async(get_role_prompt()) or ""

            # 使用共享记忆，如果为空则 fallback 到旧的 memory 表
            if memory_content and memory_content.strip():
                self.memory_content = memory_content
            else:
                self.memory_content = self._run_async(get_memory()) or ""

            # 预先格式化缓存
            self._cached_memory = self._format_memory()
            logger.bind(tag=TAG).info(
                f"从本地 lightning 数据库加载记忆成功，角色: {role_id}"
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"获取 lightning 记忆异常: {e}")

    def _run_async(self, coro):
        """同步运行异步协程"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # 如果已有运行中的事件循环，创建新的事件循环
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)

    def _format_memory(self) -> str:
        """格式化记忆内容"""
        parts = []
        if self.role_prompt:
            parts.append(f"【角色设定】\n{self.role_prompt}")
        if self.memory_content:
            parts.append(f"【长期记忆】\n{self.memory_content}")
        return "\n\n".join(parts) if parts else ""

    async def save_memory(self, msgs, session_id=None):
        """保存记忆 - 当前不实现，由 lightning-tools 的 MCP 工具处理"""
        logger.bind(tag=TAG).debug(
            "lightning memory provider: 记忆保存由 lightning-tools MCP 工具处理"
        )
        return None

    async def query_memory(self, query: str) -> str:
        """返回缓存的记忆内容（异步接口，但直接返回缓存值）"""
        return self._cached_memory or ""

    def get_cached_memory(self) -> str:
        """同步方法：返回缓存的记忆内容"""
        return self._cached_memory or ""
