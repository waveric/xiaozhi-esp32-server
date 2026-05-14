"""
Lightning Tools Memory Provider
从 lightning-tools 服务获取长期记忆和角色设定
"""
import httpx
from ..base import MemoryProviderBase, logger

TAG = __name__

# lightning-tools 服务地址
LIGHTNING_TOOLS_URL = "http://localhost:8080"


class MemoryProvider(MemoryProviderBase):
    """从 lightning-tools 获取记忆的 Memory Provider"""

    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        self.memory_content = ""
        self.role_prompt = ""
        self.lightning_url = config.get("url", LIGHTNING_TOOLS_URL)
        self._cached_memory = None  # 缓存格式化后的记忆

    def init_memory(self, role_id, llm, summary_memory=None, **kwargs):
        """初始化记忆 - 从 lightning-tools 获取记忆和角色设定"""
        super().init_memory(role_id, llm, **kwargs)

        # 从 lightning-tools 获取记忆
        try:
            # 同步调用获取记忆
            response = httpx.get(
                f"{self.lightning_url}/admin/api/context",
                headers={"device-id": role_id},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    data = result.get("data", {})
                    self.memory_content = data.get("长期记忆", "")
                    self.role_prompt = data.get("角色设定", "")
                    # 预先格式化缓存
                    self._cached_memory = self._format_memory()
                    logger.bind(tag=TAG).info(
                        f"从 lightning-tools 加载记忆成功，角色: {role_id}"
                    )
                else:
                    logger.bind(tag=TAG).warning(
                        f"lightning-tools 返回错误: {result.get('msg')}"
                    )
            else:
                logger.bind(tag=TAG).warning(
                    f"获取 lightning-tools 记忆失败: HTTP {response.status_code}"
                )
        except Exception as e:
            logger.bind(tag=TAG).error(f"获取 lightning-tools 记忆异常: {e}")

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
