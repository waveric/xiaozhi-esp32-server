# MOSS-TTS 依赖删除清单

> 本文档记录在 US-006（lightning-tools 代码复制到 xiaozhi-esp32-server）中需要执行的 MOSS-TTS 相关删除操作。

## 背景

xiaozhi-esp32-server 已内置 MOSS-TTS provider（`core/providers/tts/moss_tts.py`），通过 `conn.tts` 访问。不需要从 lightning-tools 复制 tts_service.py，因为：

1. xiaozhi 已有完整的 MOSS-TTS 集成
2. 故事音频由 lightning-tools 独立生成和缓存，通过 HTTP 提供静态文件
3. xiaozhi 不需要调用 lightning-tools 的 TTS 功能

---

## 1. 不需要复制的文件

| 文件 | 说明 |
|------|------|
| `tts_service.py` | 完整删除，不复制到 xiaozhi |

---

## 2. database.py 中的依赖删除

### 2.1 import 语句（删除）

以下 import 出现在函数内部，需要删除：

```python
# save_story() 函数中 (行 234-235)
from tts_service import generate_audio_segments

# update_story() 函数中 (行 343)
from tts_service import generate_audio_segments, delete_audio_segments

# delete_story() 函数中 (行 367)
from tts_service import delete_audio_segments
```

### 2.2 函数参数修改

| 函数 | 修改 |
|------|------|
| `save_story()` | 移除 `generate_audio: bool = True` 参数，默认不生成音频 |
| `save_story()` | 移除音频生成逻辑 (行 231-237) |
| `update_story()` | 移除音频重新生成逻辑 (行 341-350) |
| `delete_story()` | 移除音频删除逻辑 (行 365-370) |

### 2.3 具体代码块

#### save_story() - 删除以下代码块

```python
# 行 231-237
audio_segments = []
if generate_audio and text:
    try:
        from tts_service import generate_audio_segments
        audio_segments = await generate_audio_segments(text, story_id)
    except Exception as e:
        print(f"[WARN] TTS 生成失败: {e}")
```

修改为：
```python
audio_segments = []  # 不再自动生成音频
```

#### update_story() - 删除以下代码块

```python
# 行 341-350
if text is not None and text != story["content"]:
    try:
        from tts_service import generate_audio_segments, delete_audio_segments
        # 删除旧音频
        await delete_audio_segments(story_id)
        # 生成新音频
        audio_segments = await generate_audio_segments(new_content, story_id)
        audio_json = json.dumps(audio_segments, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] 重新生成音频失败: {e}")
```

修改为：
```python
# 内容变化时清空音频记录（音频由 lightning-tools 单独管理）
if text is not None and text != story["content"]:
    audio_json = "[]"  # 清空音频记录
```

#### delete_story() - 删除以下代码块

```python
# 行 365-370
try:
    from tts_service import delete_audio_segments
    await delete_audio_segments(story_id)
except Exception as e:
    print(f"[WARN] 删除音频失败: {e}")
```

---

## 3. mcp_tools.py 中的依赖删除

### 3.1 import 语句

```python
# 行 16 - 删除整行
from tts_service import ensure_story_audio, check_audio_exists, get_existing_audio_paths
```

### 3.2 需要删除的 MCP 工具函数

| 函数名 | 行号 | 说明 |
|--------|------|------|
| `get_story_with_audio()` | 87-128 | 删除整个函数 |
| `ensure_story_audio_exists()` | 132-151 | 删除整个函数 |

### 3.3 保留但需修改的函数

无。所有涉及 TTS 的 MCP 工具都应删除。

---

## 4. web_api/stories.py 中的依赖删除

### 4.1 需要删除的 API 端点

| 端点 | 方法 | 行号 | 说明 |
|------|------|------|------|
| `/stories/{story_id}/regenerate-audio` | POST | 84-110 | 删除整个端点 |

### 4.2 删除代码

```python
# 行 84-110
@router.post("/stories/{story_id}/regenerate-audio")
async def api_regenerate_audio(story_id: str):
    """重新生成故事音频"""
    story = await get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    from tts_service import generate_audio_segments, delete_audio_segments
    import json

    # 删除旧音频
    await delete_audio_segments(story_id)

    # 生成新音频
    audio_segments = await generate_audio_segments(story["content"], story_id)

    # 更新数据库
    import aiosqlite
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE stories SET audio_segments = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(audio_segments, ensure_ascii=False), story_id)
        )
        await db.commit()

    return {"success": True, "audio_segments": audio_segments}
```

---

## 5. config.py 中的配置

检查是否有 TTS_VOICE 等配置，如果有且仅被 tts_service.py 使用，可以删除：

```python
# 如果存在且仅被 tts_service.py 引用，可删除
TTS_VOICE = "Yuewen"
```

---

## 6. data/audio 目录

音频文件存储在 `data/audio/` 目录，由 lightning-tools 单独管理：
- xiaozhi 不需要复制或管理这些音频
- 音频通过 lightning-tools HTTP 服务提供（端口 8080）

---

## 执行检查清单

在 US-006 执行时，按以下步骤操作：

- [ ] 1. 不复制 `tts_service.py` 文件
- [ ] 2. 修改 `database.py`：
  - [ ] 删除 `save_story()` 中的音频生成逻辑
  - [ ] 删除 `update_story()` 中的音频重新生成逻辑
  - [ ] 删除 `delete_story()` 中的音频删除逻辑
- [ ] 3. 修改 `mcp_tools.py`：
  - [ ] 删除 tts_service import
  - [ ] 删除 `get_story_with_audio()` 函数
  - [ ] 删除 `ensure_story_audio_exists()` 函数
- [ ] 4. 修改 `web_api/stories.py`：
  - [ ] 删除 `/stories/{story_id}/regenerate-audio` 端点
- [ ] 5. 检查 `config.py`，删除仅 TTS 相关的配置
- [ ] 6. 测试：确保所有数据库操作和 MCP 工具正常工作

---

## 文档信息

- **创建时间**: 2026-05-16
- **关联 US**: US-001b (MOSS-TTS 依赖删除)
- **执行时机**: US-006 (lightning-tools 代码复制)
