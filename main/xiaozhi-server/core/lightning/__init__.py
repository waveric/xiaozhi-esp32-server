"""
lightning-tools 模块（xiaozhi-esp32-server 集成版）

提供内存、故事、词汇、经历、角色等工具函数和 Web API。
"""
from .database import (
    # 初始化
    init_db,
    # Memory
    get_memory, set_memory,
    # Role Prompt
    get_role_prompt, set_role_prompt,
    # Stories
    save_story, get_story, search_stories, list_stories, update_story, delete_story,
    # Vocabularies
    save_vocab, get_vocab, check_vocab, list_vocab, update_vocab, delete_vocab,
    # Experiences
    save_experience, get_experience, search_experiences, list_experiences, update_experience, delete_experience,
    # Sessions
    save_session, save_session_message, get_session, list_sessions, delete_session,
    # Characters
    save_character, get_character, list_characters, update_character, delete_character,
    get_character_by_name, get_current_character, set_current_character,
    # Shared Memory
    get_shared_memory, set_shared_memory,
)

from .tools import (
    # Memory tools
    get_memory as get_memory_tool,
    update_memory,
    # Story tools
    search_story, get_story_text, save_story as save_story_tool, delete_story as delete_story_tool,
    # Vocabulary tools
    check_vocabulary, update_vocabulary,
    # Experience tools
    save_experience as save_experience_tool, search_experiences as search_experiences_tool,
    # Character tools
    get_character_info, list_characters as list_characters_tool,
)

__all__ = [
    # Database
    "init_db",
    # Memory
    "get_memory", "set_memory", "get_memory_tool", "update_memory",
    # Role Prompt
    "get_role_prompt", "set_role_prompt",
    # Stories
    "save_story", "get_story", "search_stories", "list_stories", "update_story", "delete_story",
    "search_story", "get_story_text", "save_story_tool", "delete_story_tool",
    # Vocabularies
    "save_vocab", "get_vocab", "check_vocab", "list_vocab", "update_vocab", "delete_vocab",
    "check_vocabulary", "update_vocabulary",
    # Experiences
    "save_experience", "get_experience", "search_experiences", "list_experiences", "update_experience", "delete_experience",
    "save_experience_tool", "search_experiences_tool",
    # Sessions
    "save_session", "save_session_message", "get_session", "list_sessions", "delete_session",
    # Characters
    "save_character", "get_character", "list_characters", "update_character", "delete_character",
    "get_character_by_name", "get_current_character", "set_current_character",
    "get_character_info", "list_characters_tool",
    # Shared Memory
    "get_shared_memory", "set_shared_memory",
]
