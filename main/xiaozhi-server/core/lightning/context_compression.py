"""
上下文压缩模块

当对话历史过长时，自动压缩旧对话为摘要，保留最近的关键对话。
"""

import json
from typing import List, Optional
from dataclasses import dataclass

from core.utils.dialogue import Dialogue, Message


@dataclass
class CompressionConfig:
    """压缩配置"""
    enabled: bool = True
    threshold: float = 0.7  # 上下文使用率阈值
    max_context_tokens: int = 32768  # 最大上下文 token 数


class ContextCompressor:
    """
    上下文压缩器

    当上下文 token 数超过阈值时，将旧对话压缩为摘要。
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()

    def estimate_tokens(self, messages: List[Message]) -> int:
        """
        简单估算 token 数量

        使用简单的启发式方法：JSON 长度 / 3
        中文约 1.5 字符/token，英文约 4 字符/token
        """
        try:
            json_str = json.dumps([{
                "role": m.role,
                "content": m.content
            } for m in messages], ensure_ascii=False)
            return len(json_str) // 3
        except Exception:
            return 0

    async def compress(self, dialogue: Dialogue, llm) -> Dialogue:
        """
        压缩对话历史

        Args:
            dialogue: 对话对象
            llm: LLM 提供者，用于生成摘要

        Returns:
            压缩后的对话对象（原地修改）
        """
        messages = dialogue.dialogue

        # 分离消息类型
        system_msgs = [m for m in messages if m.role == "system"]
        few_shot_msgs = [m for m in messages if getattr(m, 'is_temporary', False)]

        # 实际对话消息（不含 system 和 few-shot）
        actual_msgs = [m for m in messages if m.role != "system" and not getattr(m, 'is_temporary', False)]

        # 保留最近 10 条实际对话
        recent_count = 10
        if len(actual_msgs) <= recent_count:
            return dialogue  # 无需压缩

        recent_msgs = actual_msgs[-recent_count:]
        old_msgs = actual_msgs[:-recent_count]

        if not old_msgs:
            return dialogue  # 无需压缩

        # 生成摘要
        summary_text = await self._generate_summary(old_msgs, llm)

        # 用 system Message 替代旧对话
        summary_msg = Message(
            role='system',
            content=f"[历史对话摘要]\n{summary_text}",
            is_temporary=False
        )

        # 构建新的 dialogue
        new_messages = system_msgs + few_shot_msgs + [summary_msg] + recent_msgs
        dialogue.dialogue = new_messages

        return dialogue

    async def _generate_summary(self, messages: List[Message], llm) -> str:
        """
        调用 LLM 生成摘要

        Args:
            messages: 需要摘要的消息列表
            llm: LLM 提供者

        Returns:
            摘要文本
        """
        # 构建摘要请求
        text_parts = []
        for m in messages:
            content = m.content[:200] if m.content else ""
            text_parts.append(f"{m.role}: {content}")

        text = "\n".join(text_parts)
        prompt = f"请用简洁的中文总结以下对话内容（200字以内）：\n\n{text}"

        try:
            # 调用 LLM
            response = await llm.chat(prompt)
            return response
        except Exception as e:
            return f"摘要生成失败: {str(e)}"

    def check_and_compress(self, dialogue: Dialogue, llm=None) -> bool:
        """
        检查是否需要压缩（同步版本）

        Args:
            dialogue: 对话对象
            llm: LLM 提供者（未使用，保留接口兼容）

        Returns:
            True 表示需要压缩，False 表示不需要
        """
        if not self.config.enabled:
            return False

        tokens = self.estimate_tokens(dialogue.dialogue)
        threshold_tokens = self.config.max_context_tokens * self.config.threshold

        return tokens > threshold_tokens
