# Provider 适配清单

本文档记录 xiaozhi-esp32-server 项目中所有已适配的 ASR/TTS/LLM/VAD/Intent/Memory Provider。

**当前分支**: `personal-lite`  
**参考分支**: `main`

---

## 目录

- [ASR Providers](#asr-providers)
- [TTS Providers](#tts-providers)
- [LLM Providers](#llm-providers)
- [VAD Providers](#vad-providers)
- [Intent Providers](#intent-providers)
- [Memory Providers](#memory-providers)
- [VLLM Providers](#vllm-providers)
- [Tools Providers](#tools-providers)
- [扩展指南](#扩展指南)

---

## ASR Providers

语音识别（Automatic Speech Recognition）Provider。

### 当前分支保留

| 类名 | 文件名 | 依赖库 | 需要 API Key | 本地/云端 | 状态 |
|------|--------|--------|--------------|-----------|------|
| `ASRProvider` | `aliyun.py` | `requests`, `http.client` | 是 (access_key_id + access_key_secret 或 token) | 云端 | ✅ 已保留 |
| `ASRProvider` | `aliyun_stream.py` | `websockets`, `opuslib_next`, `requests` | 是 (access_key_id + access_key_secret 或 token) | 云端 | ✅ 已保留 |
| `ASRProvider` | `aliyunbl_stream.py` | `websockets`, `opuslib_next` | 是 (api_key) | 云端 | ✅ 已保留 |
| `ASRProvider` | `fun_local.py` | `funasr`, `torch`, `psutil` | 否 | 本地 (CUDA/CPU) | ✅ 已保留 |
| `ASRProvider` | `fun_server.py` | `websockets` | 可选 (api_key) | 服务端 | ✅ 已保留 |

### 已删除（需从 main 分支拉取）

| 类名 | 文件名 | 依赖库 | 需要 API Key | 本地/云端 | 状态 |
|------|--------|--------|--------------|-----------|------|
| `ASRProvider` | `baidu.py` | `aip` (百度 AI SDK) | 是 (app_id + api_key + secret_key) | 云端 | ❌ 已删除 |
| `ASRProvider` | `doubao.py` | `websockets`, `gzip` | 是 (access_token) | 云端 | ❌ 已删除 |
| `ASRProvider` | `doubao_stream.py` | `websockets`, `opuslib_next` | 是 (access_token) | 云端 | ❌ 已删除 |
| `ASRProvider` | `openai.py` | `requests` | 是 (api_key) | 云端 | ❌ 已删除 |
| `ASRProvider` | `qwen3_asr_flash.py` | `dashscope` | 是 (api_key) | 云端 | ❌ 已删除 |
| `ASRProvider` | `sherpa_onnx_local.py` | `sherpa_onnx`, `numpy`, `modelscope` | 否 | 本地 | ❌ 已删除 |
| `ASRProvider` | `tencent.py` | `requests` | 是 (secret_id + secret_key) | 云端 | ❌ 已删除 |
| `ASRProvider` | `vosk.py` | `vosk` | 否 | 本地 | ❌ 已删除 |
| `ASRProvider` | `xunfei_stream.py` | `websockets`, `opuslib_next` | 是 (api_key + api_secret) | 云端 | ❌ 已删除 |

---

## TTS Providers

语音合成（Text-to-Speech）Provider。

### 当前分支保留

| 类名 | 文件名 | 依赖库 | 需要 API Key | 本地/云端 | 状态 |
|------|--------|--------|--------------|-----------|------|
| `TTSProvider` | `aliyun.py` | `requests` | 是 (access_key_id + access_key_secret) | 云端 | ✅ 已保留 |
| `TTSProvider` | `aliyun_stream.py` | `websockets` | 是 (access_key_id + access_key_secret) | 云端 | ✅ 已保留 |
| `TTSProvider` | `alibl_stream.py` | `websockets` | 是 (api_key) | 云端 | ✅ 已保留 |
| `TTSProvider` | `edge.py` | `edge_tts` | 否 | 云端 (免费) | ✅ 已保留 |
| `DefaultTTS` | `default.py` | - | 否 | 占位符 | ✅ 已保留 |

### 已删除（需从 main 分支拉取）

| 类名 | 文件名 | 依赖库 | 需要 API Key | 本地/云端 | 状态 |
|------|--------|--------|--------------|-----------|------|
| `TTSProvider` | `cozecn.py` | `requests` | 是 (access_token) | 云端 | ❌ 已删除 |
| `TTSProvider` | `custom.py` | `requests` | 可选 | 自定义 | ❌ 已删除 |
| `TTSProvider` | `doubao.py` | `requests` | 是 (access_token) | 云端 | ❌ 已删除 |
| `TTSProvider` | `fishspeech.py` | `requests`, `ormsgpack`, `pydantic` | 可选 (api_key) | 服务端 | ❌ 已删除 |
| `TTSProvider` | `gpt_sovits_v2.py` | `requests` | 否 | 服务端 | ❌ 已删除 |
| `TTSProvider` | `gpt_sovits_v3.py` | `requests` | 否 | 服务端 | ❌ 已删除 |
| `TTSProvider` | `huoshan_double_stream.py` | `websockets` | 是 (access_token) | 云端 | ❌ 已删除 |
| `TTSProvider` | `index_stream.py` | `aiohttp`, `requests` | 否 | 服务端 | ❌ 已删除 |
| `TTSProvider` | `minimax_httpstream.py` | `aiohttp`, `requests` | 是 (api_key) | 云端 | ❌ 已删除 |
| `TTSProvider` | `moss.py` | `aiohttp` | 否 | 本地服务 | ❌ 已删除 |
| `TTSProvider` | `openai.py` | `requests` | 是 (api_key) | 云端 | ❌ 已删除 |
| `TTSProvider` | `paddle_speech.py` | `websockets`, `numpy` | 否 | 服务端 | ❌ 已删除 |
| `TTSProvider` | `siliconflow.py` | `requests` | 是 (access_token) | 云端 | ❌ 已删除 |
| `TTSProvider` | `tencent.py` | `requests` | 是 (secret_id + secret_key) | 云端 | ❌ 已删除 |
| `TTSProvider` | `xunfei_stream.py` | `websockets` | 是 (api_key + api_secret) | 云端 | ❌ 已删除 |

---

## LLM Providers

大语言模型（Large Language Model）Provider。

### 当前分支保留

| 类名 | 文件名 | OpenAI 兼容 | 特色功能 | 状态 |
|------|--------|-------------|----------|------|
| `LLMProvider` | `openai/openai.py` | ✅ 是 | 流式响应、Function Calling、思考模式禁用 | ✅ 已保留 |

### 已删除（需从 main 分支拉取）

| 类名 | 文件名 | OpenAI 兼容 | 特色功能 | 状态 |
|------|--------|-------------|----------|------|
| `LLMProvider` | `AliBL/AliBL.py` | ❌ 否 | 阿里百炼应用、内置记忆 | ❌ 已删除 |
| `LLMProvider` | `coze/coze.py` | ❌ 否 | Coze Bot、会话管理 | ❌ 已删除 |
| `LLMProvider` | `dify/dify.py` | ❌ 否 | Dify 工作流、会话管理 | ❌ 已删除 |
| `LLMProvider` | `fastgpt/fastgpt.py` | ❌ 否 | FastGPT、变量注入 | ❌ 已删除 |
| `LLMProvider` | `gemini/gemini.py` | ❌ 否 | Google Gemini、代理支持 | ❌ 已删除 |
| `LLMProvider` | `homeassistant/homeassistant.py` | ❌ 否 | Home Assistant 集成 | ❌ 已删除 |
| `LLMProvider` | `ollama/ollama.py` | ✅ 是 | 本地 Ollama、Qwen3 思考禁用 | ❌ 已删除 |
| `LLMProvider` | `xinference/xinference.py` | ✅ 是 | 本地 Xinference | ❌ 已删除 |

---

## VAD Providers

语音活动检测（Voice Activity Detection）Provider。

### 当前分支保留

| 类名 | 文件名 | 依赖库 | 本地/云端 | 状态 |
|------|--------|--------|-----------|------|
| `VADProvider` | `silero.py` | `onnxruntime`, `opuslib_next`, `numpy` | 本地 | ✅ 已保留 |

---

## Intent Providers

意图识别 Provider。

### 当前分支保留

| 类名 | 文件名 | 依赖库 | 特色功能 | 状态 |
|------|--------|--------|----------|------|
| `IntentProvider` | `function_call/function_call.py` | - | 默认函数调用意图 | ✅ 已保留 |
| `IntentProvider` | `intent_llm/intent_llm.py` | `httpx`, `hashlib` | LLM 意图识别、缓存 | ✅ 已保留 |
| `IntentProvider` | `nointent/nointent.py` | - | 无意图识别 | ✅ 已保留 |

---

## Memory Providers

记忆管理 Provider。

### 当前分支保留

| 类名 | 文件名 | 依赖库 | 特色功能 | 状态 |
|------|--------|--------|----------|------|
| `MemoryProvider` | `lightning/lightning.py` | `httpx` | Lightning Tools HTTP 记忆 | ✅ 已保留 |
| `MemoryProvider` | `mem0ai/mem0ai.py` | `mem0` | Mem0ai 云端记忆服务 | ✅ 已保留 |
| `MemoryProvider` | `mem_local_short/mem_local_short.py` | `yaml`, `httpx` | 本地短期记忆、LLM 总结 | ✅ 已保留 |
| `MemoryProvider` | `mem_report_only/mem_report_only.py` | - | 仅上报聊天记录 | ✅ 已保留 |
| `MemoryProvider` | `nomem/nomem.py` | - | 无记忆 | ✅ 已保留 |
| `MemoryProvider` | `powermem/powermem.py` | `powermem` | PowerMem (OceanBase) | ✅ 已保留 |

---

## VLLM Providers

vLLM 推理引擎 Provider。

### 已删除（需从 main 分支拉取）

| 类名 | 文件名 | 依赖库 | OpenAI 兼容 | 状态 |
|------|--------|--------|-------------|------|
| `VLLMProvider` | `vllm/openai.py` | `openai` | ✅ 是 | ❌ 已删除 |

---

## Tools Providers

工具调用 Provider（MCP、IoT、插件等）。

### 当前分支保留

| 模块 | 目录 | 依赖库 | 特色功能 | 状态 |
|------|------|--------|----------|------|
| `device_iot` | `tools/device_iot/` | - | IoT 设备控制 | ✅ 已保留 |
| `device_mcp` | `tools/device_mcp/` | - | 设备端 MCP 客户端 | ✅ 已保留 |
| `mcp_endpoint` | `tools/mcp_endpoint/` | - | MCP 端点处理 | ✅ 已保留 |
| `server_mcp` | `tools/server_mcp/` | - | 服务端 MCP 管理 | ✅ 已保留 |
| `server_plugins` | `tools/server_plugins/` | - | 服务端插件执行 | ✅ 已保留 |
| `unified_tool_handler` | `tools/` | - | 统一工具处理 | ✅ 已保留 |
| `unified_tool_manager` | `tools/` | - | 统一工具管理 | ✅ 已保留 |

---

## 扩展指南

### 从 main 分支恢复已删除的 Provider

1. **检出单个文件**

```bash
# 恢复 ASR Provider
git checkout main -- main/xiaozhi-server/core/providers/asr/baidu.py

# 恢复 TTS Provider
git checkout main -- main/xiaozhi-server/core/providers/tts/moss.py

# 恢复 LLM Provider
git checkout main -- main/xiaozhi-server/core/providers/llm/ollama/ollama.py
```

2. **注册到 Factory**

在 `main/xiaozhi-server/core/providers/{type}/__init__.py` 中添加导入和注册：

```python
# 示例：注册新的 ASR Provider
from .baidu import ASRProvider as BaiduASRProvider

# 在 create_asr_provider 函数中添加
elif provider_name == "baidu":
    return BaiduASRProvider(config, delete_audio_file)
```

3. **添加配置**

在 `config.yaml` 中添加对应配置：

```yaml
# 示例：百度 ASR 配置
selected_asr: "baidu"
asr:
  baidu:
    app_id: "your_app_id"
    api_key: "your_api_key"
    secret_key: "your_secret_key"
    output_dir: "./audio_output"
```

### 添加新的 Provider

1. **创建 Provider 文件**

在对应目录下创建新文件，继承基类：

```python
# main/xiaozhi-server/core/providers/asr/my_asr.py
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType

class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.NON_STREAM
        # 初始化配置...

    async def speech_to_text(self, opus_data, session_id, audio_format="opus", artifacts=None):
        # 实现语音识别逻辑...
        pass
```

2. **注册到 Factory**

在 `__init__.py` 中添加导入和注册逻辑。

3. **添加配置项**

在 `config.yaml` 中添加配置。

### Provider 接口类型说明

| InterfaceType | 说明 | 适用场景 |
|---------------|------|----------|
| `NON_STREAM` | 非流式，一次性返回结果 | 简单 ASR/TTS |
| `STREAM` | 流式，实时处理音频 | 实时 ASR |
| `LOCAL` | 本地模型推理 | FunASR、Vosk |
| `SINGLE_STREAM` | 单流式 | 特殊 TTS 场景 |

### 依赖安装

不同 Provider 需要不同的依赖库：

```bash
# FunASR 本地 ASR
pip install funasr torch

# Edge TTS
pip install edge-tts

# Mem0ai 记忆
pip install mem0ai

# Silero VAD
pip install onnxruntime opuslib-next

# OpenAI LLM
pip install openai httpx
```

---

## 附录：Provider 统计

| 类型 | 当前保留 | 已删除 | 总计 |
|------|----------|--------|------|
| ASR | 5 | 9 | 14 |
| TTS | 5 | 15 | 20 |
| LLM | 1 | 8 | 9 |
| VAD | 1 | 0 | 1 |
| Intent | 3 | 0 | 3 |
| Memory | 6 | 0 | 6 |
| VLLM | 0 | 1 | 1 |
| **总计** | **21** | **33** | **54** |

---

*文档生成时间: 2026-05-16*  
*分支: personal-lite*
