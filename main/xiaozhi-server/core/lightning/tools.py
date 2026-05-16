"""
lightning-tools 工具模块（xiaozhi-esp32-server 集成版）
提供内存、故事、词汇、经历、角色等工具函数
"""
from .database import (
    get_shared_memory, set_shared_memory,
    get_story, save_story as db_save_story, delete_story as db_delete_story,
    search_stories, update_story as db_update_story,
    check_vocab, update_vocab, list_vocab, save_vocab, delete_vocab,
    save_experience as db_save_experience, search_experiences, list_experiences,
    update_experience, delete_experience as db_delete_experience,
    save_character, get_character, list_characters as db_list_characters,
    get_character_by_name, get_current_character, set_current_character
)


# ===== Memory 工具 =====

async def get_memory() -> str:
    """获取长期记忆内容，包含关于孩子的重要信息。

    返回当前保存的所有记忆内容，用于了解孩子的背景、喜好、习惯等信息。

    Returns:
        记忆内容字符串
    """
    return await get_shared_memory()


async def update_memory(content: str) -> str:
    """更新长期记忆内容。

    用于保存或更新关于孩子的重要信息，包括喜好、习惯、重要事件等。
    这些记忆会在不同对话会话间保持一致。

    Args:
        content: 新的记忆内容

    Returns:
        更新结果
    """
    await set_shared_memory(content)
    return f"记忆已更新，内容长度: {len(content)} 字符"


# ===== Story 工具 =====

async def search_story(keyword: str, limit: int = 5) -> list:
    """搜索故事库

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量限制

    Returns:
        匹配的故事列表
    """
    stories = await search_stories(keyword=keyword)
    return stories[:limit]


async def get_story_text(story_id: str) -> str:
    """获取故事的完整文本内容

    Args:
        story_id: 故事ID

    Returns:
        故事完整文本
    """
    story = await get_story(story_id)
    if story:
        return story["content"]
    return f"故事 {story_id} 不存在"


async def save_story(title: str, content: str, tags: list = None) -> dict:
    """保存新故事到故事库

    Args:
        title: 故事标题
        content: 故事内容
        tags: 标签列表

    Returns:
        保存结果，包含新故事的ID
    """
    story = await db_save_story(title=title, text=content, tags=tags)
    return story


async def delete_story(story_id: str) -> str:
    """删除故事

    Args:
        story_id: 要删除的故事ID

    Returns:
        删除结果
    """
    success = await db_delete_story(story_id)
    if success:
        return f"故事 {story_id} 已删除"
    return f"故事 {story_id} 不存在"


# ===== Vocabulary 工具 =====

async def check_vocabulary(word: str) -> dict:
    """检查词汇的熟悉度和关联经历

    Args:
        word: 要检查的词汇

    Returns:
        词汇的熟悉度信息和关联经历
    """
    result = await check_vocab(word)
    return result


async def update_vocabulary(word: str, familiarity: str = None, notes: str = None, experience_ids: list = None) -> str:
    """更新词汇信息

    Args:
        word: 词汇
        familiarity: 熟悉度 (unknown/vague/familiar)
        notes: 备注
        experience_ids: 关联的经历ID列表

    Returns:
        更新结果
    """
    # 检查词汇是否存在
    result = await check_vocab(word)
    if not result:
        # 如果词汇不存在，创建新词汇
        result = await save_vocab(word, familiarity=familiarity or "unknown", notes=notes, experience_ids=experience_ids)
    else:
        # 更新现有词汇
        result = await update_vocab(result["id"], familiarity=familiarity, notes=notes, experience_ids=experience_ids)
    return f"词汇 '{word}' 已更新"


# ===== Experience 工具 =====

async def save_experience(description: str, search_tags: str = None, event_date: str = None) -> dict:
    """保存新的经历记录

    Args:
        description: 事件描述
        search_tags: 搜索标签（空格分隔）
        event_date: 事件日期

    Returns:
        保存结果
    """
    tags_list = search_tags.split() if search_tags else None
    experience = await db_save_experience(
        description=description,
        tags=tags_list,
        event_date=event_date
    )
    return experience


async def search_experiences(keyword: str = None, limit: int = 10) -> list:
    """搜索经历记录

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量限制

    Returns:
        匹配的经历列表
    """
    experiences = await search_experiences(keyword=keyword)
    return experiences[:limit]


# ===== Character 工具 =====

async def get_character_info(name: str = None, character_id: str = None) -> dict:
    """获取指定角色的详细信息。

    通过角色名称或 ID 查询角色的完整配置信息，包括语音设置、系统提示词等。

    Args:
        name: 角色名称（支持模糊匹配）
        character_id: 角色 ID（精确匹配）

    Returns:
        角色详细信息，包含 id、name、description、voice、voice_source、
        reference_audio、system_prompt 等字段
    """
    if character_id:
        character = await get_character(character_id)
    elif name:
        character = await get_character_by_name(name)
    else:
        # 如果没有指定，返回当前角色
        character = await get_current_character()

    if character:
        return character
    return {"error": f"未找到角色: {name or character_id or '当前角色'}"}


async def list_characters() -> list:
    """获取所有角色列表"""
    return await db_list_characters()
