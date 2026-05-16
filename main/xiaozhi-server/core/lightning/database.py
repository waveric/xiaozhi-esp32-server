"""
lightning-tools 数据库模块（xiaozhi-esp32-server 集成版）
使用 aiosqlite 实现 SQLite 异步操作
"""
import aiosqlite
import os

# 数据库路径 - 使用 xiaozhi-server 的 data 目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "lightning.db")

# ===== 初始化 =====

async def init_db():
    """初始化数据库，创建所有表并插入初始数据"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 启用 WAL 模式
        await db.execute("PRAGMA journal_mode=WAL")

        # 创建 stories 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                audio_segments TEXT,
                rating INTEGER DEFAULT 0,
                play_count INTEGER DEFAULT 0,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 vocabularies 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vocabularies (
                id TEXT PRIMARY KEY,
                word TEXT NOT NULL UNIQUE,
                familiarity TEXT DEFAULT 'unknown',
                encounter_count INTEGER DEFAULT 0,
                last_heard TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 experiences 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                search_tags TEXT,
                event_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 memory 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                content TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 role_prompt 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS role_prompt (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                content TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 vocab_experiences 关联表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vocab_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vocab_id TEXT NOT NULL,
                experience_id TEXT NOT NULL,
                UNIQUE(vocab_id, experience_id),
                FOREIGN KEY (vocab_id) REFERENCES vocabularies(id) ON DELETE CASCADE,
                FOREIGN KEY (experience_id) REFERENCES experiences(id) ON DELETE CASCADE
            )
        """)

        # 创建 sessions 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 session_messages 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_call TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # 创建 characters 表（角色管理）
        await db.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                voice TEXT NOT NULL,
                voice_source TEXT DEFAULT 'builtin',
                reference_audio TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 shared_memory 表（共享记忆）
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shared_memory (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                content TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 current_state 表（当前状态）
        await db.execute("""
            CREATE TABLE IF NOT EXISTS current_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_character_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 插入初始数据
        await db.execute("""
            INSERT OR IGNORE INTO memory (id, content) VALUES (1, '')
        """)
        await db.execute("""
            INSERT OR IGNORE INTO role_prompt (id, content) VALUES (1, '你是一个叫闪电的AI小狗，性格活泼可爱，喜欢和小朋友聊天。说话要简单有趣，用小朋友能听懂的语言。')
        """)
        await db.execute("""
            INSERT OR IGNORE INTO shared_memory (id, content) VALUES (1, '')
        """)
        await db.execute("""
            INSERT OR IGNORE INTO current_state (id, current_character_id) VALUES (1, NULL)
        """)

        # 数据迁移：将 memory 表内容复制到 shared_memory 表（如果 shared_memory 为空）
        async with db.execute("SELECT content FROM memory WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                await db.execute("""
                    UPDATE shared_memory SET content = ? WHERE id = 1 AND content = ''
                """, (row[0],))

        await db.commit()

        # 初始化默认角色
        await init_characters()


# ===== Memory 操作 =====

async def get_memory() -> str:
    """获取记忆内容"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT content FROM memory WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""


async def set_memory(content: str):
    """更新记忆内容"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE memory SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (content,)
        )
        await db.commit()


# ===== Role Prompt 操作 =====

async def get_role_prompt() -> str:
    """获取角色设定"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT content FROM role_prompt WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""


async def set_role_prompt(content: str):
    """更新角色设定"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE role_prompt SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (content,)
        )
        await db.commit()


# ===== Stories 操作 =====

import uuid
import json


async def save_story(title: str, text: str, tags: list = None, summary: str = None, generate_audio: bool = False) -> dict:
    """保存故事（不生成音频）"""
    story_id = str(uuid.uuid4())
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else "[]"

    # 如果未提供 summary，取前 100 字符作为摘要
    if not summary:
        summary = text[:100] + "..." if len(text) > 100 else text

    audio_json = "[]"

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO stories (id, title, summary, content, tags, audio_segments, source)
               VALUES (?, ?, ?, ?, ?, ?, 'manual')""",
            (story_id, title, summary, text, tags_json, audio_json)
        )
        await db.commit()

    return {
        "id": story_id,
        "title": title,
        "summary": summary,
        "content": text,
        "tags": tags or [],
        "audio_segments": []
    }


async def get_story(story_id: str) -> dict | None:
    """获取单个故事"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, title, summary, content, tags, audio_segments, rating, play_count, source, created_at, updated_at FROM stories WHERE id = ?",
            (story_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "title": row[1],
                    "summary": row[2],
                    "content": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "audio_segments": json.loads(row[5]) if row[5] else [],
                    "rating": row[6],
                    "play_count": row[7],
                    "source": row[8],
                    "created_at": row[9],
                    "updated_at": row[10]
                }
            return None


async def search_stories(keyword: str = None, tags: list = None) -> list:
    """搜索故事（支持关键词和标签过滤）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = "SELECT id, title, summary, content, tags, rating, play_count, source, created_at FROM stories WHERE 1=1"
        params = []

        if keyword:
            query += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
            like_pattern = f"%{keyword}%"
            params.extend([like_pattern, like_pattern, like_pattern])

        if tags:
            # 标签搜索：检查 tags JSON 是否包含任一标签
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')

        query += " ORDER BY created_at DESC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "summary": row[2],
                    "content": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "rating": row[5],
                    "play_count": row[6],
                    "source": row[7],
                    "created_at": row[8]
                }
                for row in rows
            ]


async def list_stories() -> list:
    """获取所有故事列表"""
    return await search_stories()


async def update_story(story_id: str, title: str = None, text: str = None, tags: list = None, summary: str = None) -> dict | None:
    """更新故事（不重新生成音频）"""
    story = await get_story(story_id)
    if not story:
        return None

    new_title = title if title is not None else story["title"]
    new_content = text if text is not None else story["content"]
    new_tags = tags if tags is not None else story["tags"]
    new_summary = summary if summary is not None else (new_content[:100] + "..." if len(new_content) > 100 else new_content)

    tags_json = json.dumps(new_tags, ensure_ascii=False)
    audio_json = story.get("audio_segments", "[]")

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """UPDATE stories SET title = ?, summary = ?, content = ?, tags = ?, audio_segments = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_title, new_summary, new_content, tags_json, audio_json, story_id)
        )
        await db.commit()

    return await get_story(story_id)


async def delete_story(story_id: str) -> bool:
    """删除故事"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        await db.commit()
        return cursor.rowcount > 0


# ===== Vocabularies 操作 =====

async def save_vocab(word: str, familiarity: str = "unknown", notes: str = None, experience_ids: list = None) -> dict:
    """保存词汇"""
    vocab_id = str(uuid.uuid4())

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO vocabularies (id, word, familiarity, notes)
               VALUES (?, ?, ?, ?)""",
            (vocab_id, word, familiarity, notes)
        )

        # 关联经历
        if experience_ids:
            for exp_id in experience_ids:
                await db.execute(
                    "INSERT OR IGNORE INTO vocab_experiences (vocab_id, experience_id) VALUES (?, ?)",
                    (vocab_id, exp_id)
                )

        await db.commit()

    return await get_vocab(vocab_id)


async def get_vocab(vocab_id: str) -> dict | None:
    """获取单个词汇（包含关联的经历）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 获取词汇信息
        async with db.execute(
            """SELECT id, word, familiarity, encounter_count, last_heard, notes, created_at, updated_at
               FROM vocabularies WHERE id = ?""",
            (vocab_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            vocab = {
                "id": row[0],
                "word": row[1],
                "familiarity": row[2],
                "encounter_count": row[3],
                "last_heard": row[4],
                "notes": row[5],
                "created_at": row[6],
                "updated_at": row[7],
                "linked_experiences": []
            }

        # 获取关联的经历
        async with db.execute(
            """SELECT e.id, e.description, e.search_tags, e.event_date, e.created_at
               FROM experiences e
               INNER JOIN vocab_experiences ve ON e.id = ve.experience_id
               WHERE ve.vocab_id = ?""",
            (vocab_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            vocab["linked_experiences"] = [
                {
                    "id": row[0],
                    "description": row[1],
                    "search_tags": json.loads(row[2]) if row[2] else [],
                    "event_date": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]

        return vocab


async def check_vocab(word: str) -> dict | None:
    """检查词汇是否存在，返回词汇信息和关联的经历"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 先查找词汇 ID
        async with db.execute("SELECT id FROM vocabularies WHERE word = ?", (word,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return await get_vocab(row[0])


async def list_vocab(familiarity: str = None) -> list:
    """获取词汇列表"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = """SELECT id, word, familiarity, encounter_count, last_heard, notes, created_at
                   FROM vocabularies"""
        params = []

        if familiarity:
            query += " WHERE familiarity = ?"
            params.append(familiarity)

        query += " ORDER BY created_at DESC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "word": row[1],
                    "familiarity": row[2],
                    "encounter_count": row[3],
                    "last_heard": row[4],
                    "notes": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]


async def update_vocab(vocab_id: str, word: str = None, familiarity: str = None, notes: str = None, experience_ids: list = None) -> dict | None:
    """更新词汇"""
    vocab = await get_vocab(vocab_id)
    if not vocab:
        return None

    new_word = word if word is not None else vocab["word"]
    new_familiarity = familiarity if familiarity is not None else vocab["familiarity"]
    new_notes = notes if notes is not None else vocab["notes"]

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """UPDATE vocabularies SET word = ?, familiarity = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_word, new_familiarity, new_notes, vocab_id)
        )

        # 更新经历关联
        if experience_ids is not None:
            # 先删除旧关联
            await db.execute("DELETE FROM vocab_experiences WHERE vocab_id = ?", (vocab_id,))
            # 添加新关联
            for exp_id in experience_ids:
                await db.execute(
                    "INSERT OR IGNORE INTO vocab_experiences (vocab_id, experience_id) VALUES (?, ?)",
                    (vocab_id, exp_id)
                )

        await db.commit()

    return await get_vocab(vocab_id)


async def delete_vocab(vocab_id: str) -> bool:
    """删除词汇"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 先删除关联
        await db.execute("DELETE FROM vocab_experiences WHERE vocab_id = ?", (vocab_id,))
        cursor = await db.execute("DELETE FROM vocabularies WHERE id = ?", (vocab_id,))
        await db.commit()
        return cursor.rowcount > 0


# ===== Experiences 操作 =====

async def save_experience(description: str, search_tags: list = None, event_date: str = None) -> dict:
    """保存经历"""
    exp_id = str(uuid.uuid4())
    tags_json = json.dumps(search_tags, ensure_ascii=False) if search_tags else "[]"

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO experiences (id, description, search_tags, event_date)
               VALUES (?, ?, ?, ?)""",
            (exp_id, description, tags_json, event_date)
        )
        await db.commit()

    return await get_experience(exp_id)


async def get_experience(exp_id: str) -> dict | None:
    """获取单个经历"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT id, description, search_tags, event_date, created_at, updated_at
               FROM experiences WHERE id = ?""",
            (exp_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "description": row[1],
                    "search_tags": json.loads(row[2]) if row[2] else [],
                    "event_date": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None


async def search_experiences(keyword: str = None, tags: list = None) -> list:
    """搜索经历（支持关键词和标签过滤）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = "SELECT id, description, search_tags, event_date, created_at FROM experiences WHERE 1=1"
        params = []

        if keyword:
            query += " AND (description LIKE ?)"
            params.append(f"%{keyword}%")

        if tags:
            for tag in tags:
                query += " AND search_tags LIKE ?"
                params.append(f'%"{tag}"%')

        query += " ORDER BY event_date DESC, created_at DESC"

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "description": row[1],
                    "search_tags": json.loads(row[2]) if row[2] else [],
                    "event_date": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]


async def list_experiences() -> list:
    """获取所有经历列表"""
    return await search_experiences()


async def update_experience(exp_id: str, description: str = None, search_tags: list = None, event_date: str = None) -> dict | None:
    """更新经历"""
    exp = await get_experience(exp_id)
    if not exp:
        return None

    new_description = description if description is not None else exp["description"]
    new_tags = search_tags if search_tags is not None else exp["search_tags"]
    new_date = event_date if event_date is not None else exp["event_date"]

    tags_json = json.dumps(new_tags, ensure_ascii=False)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """UPDATE experiences SET description = ?, search_tags = ?, event_date = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_description, tags_json, new_date, exp_id)
        )
        await db.commit()

    return await get_experience(exp_id)


async def delete_experience(exp_id: str) -> bool:
    """删除经历"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 先删除关联
        await db.execute("DELETE FROM vocab_experiences WHERE experience_id = ?", (exp_id,))
        cursor = await db.execute("DELETE FROM experiences WHERE id = ?", (exp_id,))
        await db.commit()
        return cursor.rowcount > 0


# ===== Sessions 操作 =====

async def save_session(title: str = None) -> dict:
    """创建新会话"""
    session_id = str(uuid.uuid4())

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, title)
        )
        await db.commit()

    return {
        "id": session_id,
        "title": title,
        "messages": []
    }


async def save_session_message(session_id: str, role: str, content: str, tool_call: str = None) -> dict:
    """保存会话消息"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO session_messages (session_id, role, content, tool_call)
               VALUES (?, ?, ?, ?)""",
            (session_id, role, content, tool_call)
        )
        await db.commit()
        return {
            "id": cursor.lastrowid,
            "session_id": session_id,
            "role": role,
            "content": content,
            "tool_call": tool_call
        }


async def get_session(session_id: str) -> dict | None:
    """获取会话及其消息"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 获取会话信息
        async with db.execute(
            "SELECT id, title, created_at FROM sessions WHERE id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            session = {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "messages": []
            }

        # 获取消息列表
        async with db.execute(
            """SELECT id, role, content, tool_call, created_at
               FROM session_messages WHERE session_id = ?
               ORDER BY created_at ASC""",
            (session_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            session["messages"] = [
                {
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "tool_call": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]

        return session


async def list_sessions() -> list:
    """获取所有会话列表"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT s.id, s.title, s.created_at,
                      (SELECT COUNT(*) FROM session_messages WHERE session_id = s.id) as message_count
               FROM sessions s
               ORDER BY s.created_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "message_count": row[3]
                }
                for row in rows
            ]


async def delete_session(session_id: str) -> bool:
    """删除会话（消息会级联删除）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
        return cursor.rowcount > 0


# ===== Characters 操作 =====

async def save_character(character_data: dict) -> dict:
    """保存角色，character_data 需包含 name 和 voice 等字段"""
    character_id = character_data.get("id") or str(uuid.uuid4())

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO characters (id, name, description, voice, voice_source, reference_audio, system_prompt, is_default, is_active, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                character_id,
                character_data.get("name", ""),
                character_data.get("description", ""),
                character_data.get("voice", ""),
                character_data.get("voice_source", "builtin"),
                character_data.get("reference_audio", ""),
                character_data.get("system_prompt", ""),
                character_data.get("is_default", 0),
                character_data.get("is_active", 1),
                character_data.get("sort_order", 0),
            )
        )
        await db.commit()

    return await get_character(character_id)


async def get_character(character_id: str) -> dict | None:
    """获取单个角色"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT id, name, description, voice, voice_source, reference_audio, system_prompt,
                      is_default, is_active, sort_order, created_at, updated_at
               FROM characters WHERE id = ?""",
            (character_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "voice": row[3],
                    "voice_source": row[4],
                    "reference_audio": row[5],
                    "system_prompt": row[6],
                    "is_default": row[7],
                    "is_active": row[8],
                    "sort_order": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                }
            return None


async def list_characters() -> list:
    """获取所有角色列表，按 sort_order 排序"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT id, name, description, voice, voice_source, reference_audio, system_prompt,
                      is_default, is_active, sort_order, created_at, updated_at
               FROM characters
               ORDER BY sort_order ASC, created_at ASC"""
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "voice": row[3],
                    "voice_source": row[4],
                    "reference_audio": row[5],
                    "system_prompt": row[6],
                    "is_default": row[7],
                    "is_active": row[8],
                    "sort_order": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                }
                for row in rows
            ]


async def update_character(character_id: str, data: dict) -> dict | None:
    """更新角色，data 为需要更新的字段字典"""
    character = await get_character(character_id)
    if not character:
        return None

    # 合并更新数据
    new_name = data.get("name", character["name"])
    new_description = data.get("description", character["description"])
    new_voice = data.get("voice", character["voice"])
    new_voice_source = data.get("voice_source", character["voice_source"])
    new_reference_audio = data.get("reference_audio", character["reference_audio"])
    new_system_prompt = data.get("system_prompt", character["system_prompt"])
    new_is_default = data.get("is_default", character["is_default"])
    new_is_active = data.get("is_active", character["is_active"])
    new_sort_order = data.get("sort_order", character["sort_order"])

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 如果设置为默认角色，先取消其他默认角色
        if new_is_default:
            await db.execute(
                "UPDATE characters SET is_default = 0, updated_at = CURRENT_TIMESTAMP WHERE is_default = 1"
            )

        await db.execute(
            """UPDATE characters SET name = ?, description = ?, voice = ?, voice_source = ?,
               reference_audio = ?, system_prompt = ?, is_default = ?, is_active = ?,
               sort_order = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                new_name, new_description, new_voice, new_voice_source,
                new_reference_audio, new_system_prompt, new_is_default,
                new_is_active, new_sort_order, character_id
            )
        )
        await db.commit()

    return await get_character(character_id)


async def delete_character(character_id: str) -> bool:
    """删除角色"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_character_by_name(name: str) -> dict | None:
    """按名称查找角色，支持模糊匹配"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 先精确匹配
        async with db.execute(
            """SELECT id FROM characters WHERE name = ?""",
            (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return await get_character(row[0])

        # 再模糊匹配
        async with db.execute(
            """SELECT id FROM characters WHERE name LIKE ? LIMIT 1""",
            (f"%{name}%",)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return await get_character(row[0])

        return None


async def get_current_character() -> dict | None:
    """获取当前激活的角色"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT current_character_id FROM current_state WHERE id = 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return await get_character(row[0])

        # 如果没有设置当前角色，返回默认角色
        async with db.execute(
            "SELECT id FROM characters WHERE is_default = 1 AND is_active = 1 LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return await get_character(row[0])

        # 如果没有默认角色，返回第一个激活的角色
        async with db.execute(
            "SELECT id FROM characters WHERE is_active = 1 ORDER BY sort_order ASC, created_at ASC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return await get_character(row[0])

        return None


async def set_current_character(character_id: str) -> bool:
    """设置当前角色"""
    # 先验证角色存在且激活
    character = await get_character(character_id)
    if not character:
        return False

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE current_state SET current_character_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (character_id,)
        )
        await db.commit()
        return True


async def init_characters():
    """初始化默认角色（仅在无角色时插入）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 检查是否已有角色
        async with db.execute("SELECT COUNT(*) FROM characters") as cursor:
            row = await cursor.fetchone()
            if row[0] > 0:
                return

        # 插入默认角色"姐姐"
        default_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO characters (id, name, description, voice, voice_source, reference_audio, system_prompt, is_default, is_active, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                default_id,
                '姐姐',
                '乐乐的姐姐，说话温柔有耐心，带一点台湾腔的口音',
                'Yuewen',
                'builtin',
                '',
                '你是乐乐的姐姐，说话温柔有耐心，带一点台湾腔的口音。你喜欢陪乐乐聊天讲故事，会耐心回答每一个问题。说话亲切自然，像真的姐姐一样关心弟弟。用词简单，偶尔带点可爱的语气词。你了解乐乐的喜好和习惯，会在对话中自然地体现这份了解。',
                1,
                1,
                0,
            )
        )

        # 设置默认角色为当前角色
        await db.execute(
            "UPDATE current_state SET current_character_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (default_id,)
        )

        await db.commit()


# ===== Shared Memory 操作 =====

async def get_shared_memory() -> str:
    """获取共享记忆内容"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT content FROM shared_memory WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""


async def set_shared_memory(content: str):
    """更新共享记忆内容"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE shared_memory SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (content,)
        )
        await db.commit()
