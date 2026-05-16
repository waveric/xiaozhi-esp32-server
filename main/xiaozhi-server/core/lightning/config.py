"""
lightning-tools 配置模块（xiaozhi-esp32-server 集成版）
"""
import os

# 项目根目录 - 指向 xiaozhi-server 目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据库路径 - 使用 xiaozhi-server 的 data 目录
DATABASE_PATH = os.path.join(BASE_DIR, "data", "lightning.db")

# agent-base-prompt.txt 路径（用于读写行为规则）
AGENT_BASE_PROMPT_PATH = os.path.join(BASE_DIR, "agent-base-prompt.txt")
