"""
lightning-tools 内置工具插件
直接调用 core/lightning/tools.py 中的函数，无需通过 MCP 远程调用
"""
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


# ===== Function Schemas =====

# Memory 工具
get_memory_function_desc = {
    "type": "function",
    "function": {
        "name": "get_memory",
        "description": "获取长期记忆内容，包含关于孩子的重要信息。返回当前保存的所有记忆内容，用于了解孩子的背景、喜好、习惯等信息。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

update_memory_function_desc = {
    "type": "function",
    "function": {
        "name": "update_memory",
        "description": "更新长期记忆内容。用于保存或更新关于孩子的重要信息，包括喜好、习惯、重要事件等。这些记忆会在不同对话会话间保持一致。",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "新的记忆内容",
                }
            },
            "required": ["content"],
        },
    },
}

# Story 工具
search_story_function_desc = {
    "type": "function",
    "function": {
        "name": "search_story",
        "description": "搜索故事库中的故事。根据关键词查找相关的故事。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制，默认5",
                }
            },
            "required": ["keyword"],
        },
    },
}

get_story_text_function_desc = {
    "type": "function",
    "function": {
        "name": "get_story_text",
        "description": "获取故事的完整文本内容。根据故事ID获取故事的详细内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "string",
                    "description": "故事ID",
                }
            },
            "required": ["story_id"],
        },
    },
}

save_story_function_desc = {
    "type": "function",
    "function": {
        "name": "save_story",
        "description": "保存新故事到故事库。将一个新的故事保存到数据库中。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "故事标题",
                },
                "content": {
                    "type": "string",
                    "description": "故事内容",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签列表，用于分类和搜索",
                }
            },
            "required": ["title", "content"],
        },
    },
}

delete_story_function_desc = {
    "type": "function",
    "function": {
        "name": "delete_story",
        "description": "从故事库中删除故事。根据故事ID删除指定的故事。",
        "parameters": {
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "string",
                    "description": "要删除的故事ID",
                }
            },
            "required": ["story_id"],
        },
    },
}

# Vocabulary 工具
check_vocabulary_function_desc = {
    "type": "function",
    "function": {
        "name": "check_vocabulary",
        "description": "检查词汇的熟悉度和关联经历。了解孩子对某个词汇的掌握程度。",
        "parameters": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "要检查的词汇",
                }
            },
            "required": ["word"],
        },
    },
}

update_vocabulary_function_desc = {
    "type": "function",
    "function": {
        "name": "update_vocabulary",
        "description": "更新词汇信息。记录或更新孩子对某个词汇的熟悉度和相关备注。",
        "parameters": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "词汇",
                },
                "familiarity": {
                    "type": "string",
                    "enum": ["unknown", "vague", "familiar"],
                    "description": "熟悉度：unknown(不认识)、vague(模糊)、familiar(熟悉)",
                },
                "notes": {
                    "type": "string",
                    "description": "备注信息",
                },
                "experience_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "关联的经历ID列表",
                }
            },
            "required": ["word"],
        },
    },
}

# Experience 工具
save_experience_function_desc = {
    "type": "function",
    "function": {
        "name": "save_experience",
        "description": "保存新的经历记录。记录孩子生活中的重要事件或经历。",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "事件描述",
                },
                "search_tags": {
                    "type": "string",
                    "description": "搜索标签，用空格分隔多个标签",
                },
                "event_date": {
                    "type": "string",
                    "description": "事件日期，格式 YYYY-MM-DD",
                }
            },
            "required": ["description"],
        },
    },
}

search_experiences_function_desc = {
    "type": "function",
    "function": {
        "name": "search_experiences",
        "description": "搜索经历记录。根据关键词查找相关的经历。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制，默认10",
                }
            },
            "required": [],
        },
    },
}

# Character 工具
get_character_info_function_desc = {
    "type": "function",
    "function": {
        "name": "get_character_info",
        "description": "获取指定角色的详细信息。通过角色名称或 ID 查询角色的完整配置信息，包括语音设置、系统提示词等。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "角色名称（支持模糊匹配）",
                },
                "character_id": {
                    "type": "string",
                    "description": "角色 ID（精确匹配）",
                }
            },
            "required": [],
        },
    },
}


# ===== 工具实现 =====

@register_function("get_memory", get_memory_function_desc, ToolType.WAIT)
async def get_memory(conn: "ConnectionHandler" = None):
    """获取长期记忆内容"""
    try:
        from core.lightning.tools import get_memory as _get_memory
        result = await _get_memory()
        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取记忆失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"获取记忆失败: {str(e)}",
            response=None,
        )


@register_function("update_memory", update_memory_function_desc, ToolType.WAIT)
async def update_memory(content: str, conn: "ConnectionHandler" = None):
    """更新长期记忆内容"""
    try:
        from core.lightning.tools import update_memory as _update_memory
        result = await _update_memory(content)
        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"更新记忆失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"更新记忆失败: {str(e)}",
            response=None,
        )


@register_function("search_story", search_story_function_desc, ToolType.WAIT)
async def search_story(keyword: str, limit: int = 5, conn: "ConnectionHandler" = None):
    """搜索故事库"""
    try:
        from core.lightning.tools import search_story as _search_story
        result = await _search_story(keyword, limit)
        return ActionResponse(
            action=Action.REQLLM,
            result=str(result),
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"搜索故事失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"搜索故事失败: {str(e)}",
            response=None,
        )


@register_function("get_story_text", get_story_text_function_desc, ToolType.WAIT)
async def get_story_text(story_id: str, conn: "ConnectionHandler" = None):
    """获取故事文本"""
    try:
        from core.lightning.tools import get_story_text as _get_story_text
        result = await _get_story_text(story_id)
        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取故事文本失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"获取故事文本失败: {str(e)}",
            response=None,
        )


@register_function("save_story", save_story_function_desc, ToolType.WAIT)
async def save_story(title: str, content: str, tags: list = None, conn: "ConnectionHandler" = None):
    """保存故事"""
    try:
        from core.lightning.tools import save_story as _save_story
        result = await _save_story(title, content, tags)
        return ActionResponse(
            action=Action.REQLLM,
            result=f"故事已保存: {result}",
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"保存故事失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"保存故事失败: {str(e)}",
            response=None,
        )


@register_function("delete_story", delete_story_function_desc, ToolType.WAIT)
async def delete_story(story_id: str, conn: "ConnectionHandler" = None):
    """删除故事"""
    try:
        from core.lightning.tools import delete_story as _delete_story
        result = await _delete_story(story_id)
        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"删除故事失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"删除故事失败: {str(e)}",
            response=None,
        )


@register_function("check_vocabulary", check_vocabulary_function_desc, ToolType.WAIT)
async def check_vocabulary(word: str, conn: "ConnectionHandler" = None):
    """检查词汇熟悉度"""
    try:
        from core.lightning.tools import check_vocabulary as _check_vocabulary
        result = await _check_vocabulary(word)
        return ActionResponse(
            action=Action.REQLLM,
            result=str(result),
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"检查词汇失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"检查词汇失败: {str(e)}",
            response=None,
        )


@register_function("update_vocabulary", update_vocabulary_function_desc, ToolType.WAIT)
async def update_vocabulary(
    word: str,
    familiarity: str = None,
    notes: str = None,
    experience_ids: list = None,
    conn: "ConnectionHandler" = None
):
    """更新词汇信息"""
    try:
        from core.lightning.tools import update_vocabulary as _update_vocabulary
        result = await _update_vocabulary(word, familiarity, notes, experience_ids)
        return ActionResponse(
            action=Action.REQLLM,
            result=result,
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"更新词汇失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"更新词汇失败: {str(e)}",
            response=None,
        )


@register_function("save_experience", save_experience_function_desc, ToolType.WAIT)
async def save_experience(
    description: str,
    search_tags: str = None,
    event_date: str = None,
    conn: "ConnectionHandler" = None
):
    """保存经历记录"""
    try:
        from core.lightning.tools import save_experience as _save_experience
        result = await _save_experience(description, search_tags, event_date)
        return ActionResponse(
            action=Action.REQLLM,
            result=f"经历已保存: {result}",
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"保存经历失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"保存经历失败: {str(e)}",
            response=None,
        )


@register_function("search_experiences", search_experiences_function_desc, ToolType.WAIT)
async def search_experiences(keyword: str = None, limit: int = 10, conn: "ConnectionHandler" = None):
    """搜索经历记录"""
    try:
        from core.lightning.tools import search_experiences as _search_experiences
        result = await _search_experiences(keyword, limit)
        return ActionResponse(
            action=Action.REQLLM,
            result=str(result),
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"搜索经历失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"搜索经历失败: {str(e)}",
            response=None,
        )


@register_function("get_character_info", get_character_info_function_desc, ToolType.WAIT)
async def get_character_info(name: str = None, character_id: str = None, conn: "ConnectionHandler" = None):
    """获取角色信息"""
    try:
        from core.lightning.tools import get_character_info as _get_character_info
        result = await _get_character_info(name, character_id)
        return ActionResponse(
            action=Action.REQLLM,
            result=str(result),
            response=None,
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取角色信息失败: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"获取角色信息失败: {str(e)}",
            response=None,
        )
