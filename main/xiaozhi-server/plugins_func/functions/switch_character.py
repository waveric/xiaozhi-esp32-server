"""
角色切换插件
从 lightning-tools API 获取角色定义，切换 TTS 音色和系统提示词
"""
import requests
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# lightning-tools API 基础 URL
LIGHTNING_TOOLS_API = "http://localhost:8080/admin/api"


def _fetch_characters():
    """从 lightning-tools 获取角色列表"""
    try:
        response = requests.get(f"{LIGHTNING_TOOLS_API}/characters", timeout=5)
        if response.ok:
            data = response.json()
            return data.get("characters", [])
        return []
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取角色列表失败: {e}")
        return []


def _fetch_character_by_name(character_name: str):
    """根据角色名称获取角色详情"""
    characters = _fetch_characters()
    for char in characters:
        if char.get("name") == character_name:
            # 如果有 id，获取完整角色信息
            char_id = char.get("id")
            if char_id:
                try:
                    response = requests.get(
                        f"{LIGHTNING_TOOLS_API}/characters/{char_id}", timeout=5
                    )
                    if response.ok:
                        return response.json()
                except Exception as e:
                    logger.bind(tag=TAG).error(f"获取角色详情失败: {e}")
            return char
    return None


def _build_switch_character_description():
    """构建 switch_character 的 function description，包含可用角色列表"""
    # 延迟获取角色列表，避免模块加载时依赖 lightning-tools
    try:
        characters = _fetch_characters()
        character_names = [char.get("name", "") for char in characters if char.get("name")]

        if character_names:
            available_chars = "、".join(character_names)
            description = (
                f"切换助手角色/性格。可用角色：[{available_chars}]。"
                f"当用户想切换角色、改变性格、或想让我扮演特定角色时调用。"
            )
        else:
            description = (
                "切换助手角色/性格。"
                "当用户想切换角色、改变性格、或想让我扮演特定角色时调用。"
            )
    except Exception as e:
        logger.bind(tag=TAG).warning(f"构建角色描述时获取角色列表失败: {e}")
        description = (
            "切换助手角色/性格。"
            "当用户想切换角色、改变性格、或想让我扮演特定角色时调用。"
        )

    return {
        "type": "function",
        "function": {
            "name": "switch_character",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "character_name": {
                        "type": "string",
                        "description": "要切换的角色名称",
                    }
                },
                "required": ["character_name"],
            },
        },
    }


# 使用默认描述，避免模块加载时依赖 lightning-tools
# 实际调用时会动态获取角色列表
switch_character_function_desc = {
    "type": "function",
    "function": {
        "name": "switch_character",
        "description": "切换助手角色/性格。当用户想切换角色、改变性格、或想让我扮演特定角色时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "character_name": {
                    "type": "string",
                    "description": "要切换的角色名称",
                }
            },
            "required": ["character_name"],
        },
    },
}

list_characters_function_desc = {
    "type": "function",
    "function": {
        "name": "list_characters",
        "description": "列出所有可用的角色。当用户想知道有哪些角色可以切换时调用。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


@register_function("switch_character", switch_character_function_desc, ToolType.SYSTEM_CTL)
def switch_character(conn: "ConnectionHandler", character_name: str):
    """
    切换角色

    1. 从 lightning-tools API 获取角色定义
    2. 切换 TTS 音色
    3. 使用 prompt_manager.build_enhanced_prompt() 渲染完整 prompt
    4. 应用新 prompt
    5. 清空对话历史，仅保留 system message
    """
    try:
        # 1. 获取角色定义
        character = _fetch_character_by_name(character_name)
        if not character:
            logger.bind(tag=TAG).warning(f"角色不存在: {character_name}")
            return ActionResponse(
                action=Action.RESPONSE,
                result="角色切换失败",
                response=f"没有找到名为「{character_name}」的角色。请使用 list_characters 查看可用角色。",
            )

        # 2. 切换 TTS 音色
        voice = character.get("voice")
        if voice:
            # 确保 TTS 已初始化
            if hasattr(conn, "tts") and conn.tts is not None:
                conn.tts.voice = voice
                logger.bind(tag=TAG).info(f"已切换 TTS 音色: {voice}")
            else:
                # TTS 尚未初始化，调用初始化
                logger.bind(tag=TAG).info(f"TTS 尚未初始化，正在初始化...")
                try:
                    tts = conn._initialize_tts()
                    if tts:
                        tts.voice = voice
                        conn.tts = tts
                        # 打开音频通道
                        import asyncio
                        asyncio.run_coroutine_threadsafe(
                            tts.open_audio_channels(conn), conn.loop
                        )
                        logger.bind(tag=TAG).info(f"已初始化 TTS 并切换音色: {voice}")
                    else:
                        logger.bind(tag=TAG).warning(f"TTS 初始化失败，无法切换音色")
                except Exception as e:
                    logger.bind(tag=TAG).error(f"初始化 TTS 失败: {e}")

        # 3. 使用 prompt_manager.build_enhanced_prompt() 渲染完整 prompt
        system_prompt = character.get("system_prompt", "")
        if not system_prompt:
            # 如果角色没有定义 system_prompt，使用默认 prompt
            system_prompt = conn.config.get("prompt", "")

        enhanced_prompt = conn.prompt_manager.build_enhanced_prompt(
            user_prompt=system_prompt,
            device_id=conn.device_id,
            client_ip=conn.client_ip,
        )

        # 4. 应用新 prompt
        conn.change_system_prompt(enhanced_prompt)
        logger.bind(tag=TAG).info(f"已切换系统提示词，角色: {character_name}")

        # 5. 清空对话历史，仅保留 system message
        system_message = next(
            (msg for msg in conn.dialogue.dialogue if msg.role == "system"), None
        )
        if system_message:
            conn.dialogue.dialogue = [system_message]
        else:
            conn.dialogue.dialogue = []
            logger.bind(tag=TAG).warning("未找到 system message，对话历史已清空")

        logger.bind(tag=TAG).info(f"角色切换成功: {character_name}")
        return ActionResponse(
            action=Action.RESPONSE,
            result="角色切换成功",
            response=f"已切换为「{character_name}」。{character.get('description', '')}",
        )

    except Exception as e:
        logger.bind(tag=TAG).error(f"切换角色失败: {e}")
        return ActionResponse(
            action=Action.RESPONSE,
            result="角色切换失败",
            response=f"切换角色时出错: {str(e)}",
        )


@register_function("list_characters", list_characters_function_desc, ToolType.WAIT)
def list_characters():
    """
    列出所有可用角色
    """
    try:
        characters = _fetch_characters()
        if not characters:
            return ActionResponse(
                action=Action.REQLLM,
                result="当前没有可用的角色。请在 lightning-tools 管理界面添加角色。",
                response=None,
            )

        # 构建角色列表信息
        char_list = []
        for char in characters:
            name = char.get("name", "未命名")
            desc = char.get("description", "")
            voice = char.get("voice", "")
            char_info = f"「{name}」"
            if desc:
                char_info += f" - {desc}"
            if voice:
                char_info += f" (音色: {voice})"
            char_list.append(char_info)

        result = "可用角色列表：\n" + "\n".join(f"{i+1}. {info}" for i, info in enumerate(char_list))
        result += "\n\n使用 switch_character 角色名 来切换角色。"

        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )

    except Exception as e:
        logger.bind(tag=TAG).error(f"获取角色列表失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"获取角色列表失败: {str(e)}",
            response=None,
        )
