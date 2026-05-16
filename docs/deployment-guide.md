# 部署环境指南

本文档记录 xiaozhi-esp32-server 的完整部署环境信息、依赖、配置步骤。

**目标读者**: Agent 自动化部署，所有命令可直接复制执行。

---

## 1. 系统要求

### 1.1 基本要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ (推荐 3.10.x) |
| 操作系统 | Windows 10/11, Linux (Ubuntu 20.04+), macOS |
| 内存 | 最低 4GB，推荐 8GB+ |
| 磁盘 | 最低 5GB (含模型文件) |

### 1.2 GPU 支持 (可选)

| 项目 | 要求 |
|------|------|
| NVIDIA GPU | CUDA 12.1+ 兼容显卡 |
| NVIDIA 驱动 | 525.60.13+ |
| CUDA Toolkit | 12.1+ |

**GPU 用途**:
- FunASR 本地语音识别加速
- MOSS-TTS 本地语音合成加速

**CPU 模式**: 无 GPU 也可正常运行，使用 ONNX Runtime 推理。

---

## 2. Python 依赖

### 2.1 核心依赖 (requirements.txt)

```
# 音频处理
torch>=2.2.2              # 深度学习框架
torchaudio>=2.2.2         # 音频处理
opuslib_next==1.1.5       # Opus 编解码
pydub==0.25.1             # 音频格式转换

# 语音识别
funasr==1.2.7             # 阿里 FunASR 语音识别
sherpa_onnx==1.12.29      # Sherpa ONNX 语音识别
vosk==0.3.45              # Vosk 离线语音识别
silero_vad==6.1.0         # 语音活动检测

# 语音合成
edge_tts==7.2.6           # 微软 Edge TTS

# LLM 接口
openai==2.8.1             # OpenAI 兼容 API
google-generativeai==0.8.5  # Gemini API

# 网络通信
websockets==14.2          # WebSocket 服务器
aiohttp==3.13.2           # 异步 HTTP 客户端
httpx==0.28.1             # HTTP 客户端

# MCP 工具
mcp==1.22.0               # Model Context Protocol
mcp-proxy==0.10.0         # MCP 代理

# 记忆功能
mem0ai==1.0.0             # Mem0 记忆服务
powermem>=0.3.1           # PowerMem 记忆组件

# 配置与日志
pyyml==0.0.2              # YAML 解析
ruamel.yaml==0.18.16      # YAML 高级解析
loguru==0.7.3             # 日志框架

# 其他
requests==2.32.5
numpy==1.26.4
modelscope==1.32.0        # 模型下载
```

### 2.2 CUDA 版本依赖 (requirements-cuda.txt)

使用 CUDA 加速时，需要额外安装 CUDA 版本的 PyTorch：

```bash
# CUDA 12.1 版本
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

---

## 3. config.yaml 配置说明

### 3.1 配置文件位置

```
项目根目录/
├── main/
│   └── xiaozhi-server/
│       ├── config.yaml        # 默认配置 (只读)
│       └── data/
│           └── .config.yaml   # 用户配置 (优先级更高)
```

**配置优先级**: `data/.config.yaml` > `config.yaml`

### 3.2 必填配置项

```yaml
# 服务器网络配置
server:
  ip: 0.0.0.0                    # 监听地址，默认 0.0.0.0
  port: 8000                     # WebSocket 端口
  http_port: 8003                # HTTP API 端口
  websocket: ws://你的IP:8000/xiaozhi/v1/  # ESP32 连接地址

# 模块选择
selected_module:
  VAD: SileroVAD                 # 语音活动检测
  ASR: FunASR                    # 语音识别
  LLM: ChatGLMLLM                # 大语言模型
  TTS: EdgeTTS                   # 语音合成
  Memory: nomem                  # 记忆模块 (可选)
  Intent: function_call          # 意图识别

# LLM 密钥配置 (必填，根据选择的 LLM)
LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: 你的智谱API密钥
```

### 3.3 常用 LLM 配置示例

#### ChatGLMLLM (免费)

```yaml
LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: 你的智谱API密钥  # 获取: https://bigmodel.cn/usercenter/proj-mgmt/apikeys
```

#### DeepSeekLLM

```yaml
LLM:
  DeepSeekLLM:
    type: openai
    model_name: deepseek-chat
    url: https://api.deepseek.com
    api_key: 你的DeepSeek密钥  # 获取: https://platform.deepseek.com/
```

#### DoubaoLLM (火山引擎)

```yaml
LLM:
  DoubaoLLM:
    type: openai
    base_url: https://ark.cn-beijing.volces.com/api/v3
    model_name: doubao-1-5-pro-32k-250115
    api_key: 你的火山引擎密钥  # 获取: https://console.volcengine.com/ark/apiKey
```

### 3.4 ASR 配置

#### FunASR 本地 (默认)

```yaml
ASR:
  FunASR:
    type: fun_local
    model_dir: models/SenseVoiceSmall
    output_dir: tmp/
```

#### 云端 ASR (可选)

```yaml
ASR:
  AliyunBLStreamASR:
    type: aliyunbl_stream
    api_key: 你的阿里云百炼API密钥
    model: paraformer-realtime-v2
```

### 3.5 TTS 配置

#### EdgeTTS (免费，默认)

```yaml
TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural
    output_dir: tmp/
```

#### MossTTS (本地 CUDA)

```yaml
TTS:
  MossTTS:
    type: moss
    voice: Yuewen
    server_url: http://localhost:18083
    output_dir: tmp/
```

#### 火山引擎流式 TTS

```yaml
TTS:
  HuoshanDoubleStreamTTS:
    type: huoshan_double_stream
    ws_url: wss://openspeech.bytedance.com/api/v3/tts/bidirection
    appid: 你的appid
    access_token: 你的access_token
    resource_id: volc.service_type.10029
    speaker: zh_female_wanwanxiaohe_moon_bigtts
```

### 3.6 Memory 配置

```yaml
Memory:
  # 不使用记忆
  nomem:
    type: nomem

  # 本地短期记忆
  mem_local_short:
    type: mem_local_short
    llm: ChatGLMLLM

  # lightning-tools 服务
  lightning:
    type: lightning
    url: "http://localhost:8080"
```

---

## 4. 环境变量列表

### 4.1 支持的环境变量

| 变量名 | 用途 | 获取方式 |
|--------|------|----------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key | https://bailian.console.aliyun.com/#/api-key |

### 4.2 使用方式

环境变量为可选配置，主要用于性能测试工具。正常情况下在 `config.yaml` 中配置即可。

```bash
# Linux/macOS
export DASHSCOPE_API_KEY=your_api_key

# Windows CMD
set DASHSCOPE_API_KEY=your_api_key

# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key"
```

---

## 5. 端口规划

### 5.1 默认端口

| 端口 | 服务 | 用途 |
|------|------|------|
| 8000 | WebSocket | ESP32 设备连接，实时语音对话 |
| 8003 | HTTP API | OTA 固件更新、Vision API |

### 5.2 防火墙配置

#### Linux (ufw)

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8003/tcp
```

#### Linux (firewalld)

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --reload
```

#### Windows 防火墙

```powershell
# 管理员 PowerShell
New-NetFirewallRule -DisplayName "Xiaozhi WebSocket" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Xiaozhi HTTP" -Direction Inbound -Port 8003 -Protocol TCP -Action Allow
```

---

## 6. GPU vs CPU 切换说明

### 6.1 CUDA 模式 (GPU 加速)

**安装 CUDA 版 PyTorch**:

```bash
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

**验证 CUDA 可用**:

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

### 6.2 CPU 模式

**安装 CPU 版 PyTorch**:

```bash
pip install torch==2.2.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cpu
```

### 6.3 模式切换

无需修改配置文件，系统自动检测 CUDA 可用性：

- CUDA 可用 → 使用 GPU 加速
- CUDA 不可用 → 回退到 CPU (ONNX Runtime)

---

## 7. 云端部署步骤

### 7.1 从零开始的完整命令

```bash
# 1. 安装系统依赖 (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git

# 2. 克隆项目
git clone https://github.com/xinnan-tech/xiaozhi-esp32-server.git
cd xiaozhi-esp32-server

# 3. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 4. 安装依赖
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r main/xiaozhi-server/requirements.txt

# 5. 创建必要目录
mkdir -p main/xiaozhi-server/data
mkdir -p main/xiaozhi-server/models/SenseVoiceSmall
mkdir -p main/xiaozhi-server/tmp

# 6. 下载 ASR 模型 (约 400MB)
wget -O main/xiaozhi-server/models/SenseVoiceSmall/model.pt \
  https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt

# 7. 创建配置文件
cat > main/xiaozhi-server/data/.config.yaml << 'EOF'
server:
  websocket: ws://你的服务器IP:8000/xiaozhi/v1/

selected_module:
  LLM: ChatGLMLLM

LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: 你的智谱API密钥
EOF

# 8. 启动服务
cd main/xiaozhi-server
python app.py
```

### 7.2 CUDA 云端部署

```bash
# 安装 CUDA 版 PyTorch
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# 其他步骤同上
```

---

## 8. 本地部署步骤 (Windows)

### 8.1 安装 Anaconda

1. 下载 Anaconda: https://www.anaconda.com/download
2. 安装后打开 **Anaconda Prompt (管理员)**

### 8.2 创建环境并安装依赖

```cmd
# 创建虚拟环境
conda remove -n xiaozhi-esp32-server --all -y
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server

# 安装系统依赖
conda install libopus -y
conda install ffmpeg -y

# 进入项目目录
cd f:\robot-dog\xiaozhi-esp32-server\main\xiaozhi-server

# 安装 Python 依赖
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

### 8.3 CUDA 版本 (可选)

```cmd
# 安装 CUDA 版 PyTorch
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

### 8.4 下载模型文件

1. 下载 SenseVoiceSmall 模型:
   - 魔搭: https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt
   - 百度网盘: https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna

2. 放置到: `models/SenseVoiceSmall/model.pt`

### 8.5 创建配置文件

在 `main/xiaozhi-server/data/` 目录创建 `.config.yaml`:

```yaml
server:
  websocket: ws://你的电脑IP:8000/xiaozhi/v1/

selected_module:
  LLM: ChatGLMLLM

LLM:
  ChatGLMLLM:
    api_key: 你的智谱API密钥
```

### 8.6 启动服务

```cmd
conda activate xiaozhi-esp32-server
cd f:\robot-dog\xiaozhi-esp32-server\main\xiaozhi-server
python app.py
```

### 8.7 验证启动成功

看到以下日志表示启动成功:

```
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-OTA接口是           http://192.168.4.123:8003/xiaozhi/ota/
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-Websocket地址是     ws://192.168.4.123:8000/xiaozhi/v1/
```

---

## 9. 常见问题排查

### 9.1 端口冲突

**现象**: 启动失败，提示端口已被占用

**排查**:

```bash
# Linux
lsof -i :8000
lsof -i :8003

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :8003
```

**解决**:

```yaml
# 修改 data/.config.yaml
server:
  port: 8001      # 改为其他端口
  http_port: 8004 # 改为其他端口
```

### 9.2 CUDA 不可用

**现象**: 日志显示 `CUDA not available`，使用 CPU 模式

**排查**:

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**解决**:

1. 更新 NVIDIA 驱动到最新版本
2. 重新安装 CUDA 版 PyTorch:
   ```bash
   pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
   ```

### 9.3 API Key 无效

**现象**: LLM 调用失败，返回认证错误

**排查步骤**:

1. 检查 API Key 是否正确配置在 `data/.config.yaml`
2. 检查 API Key 是否过期或余额不足
3. 使用 curl 测试 API 连通性:

```bash
# 测试智谱 API
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer 你的API密钥" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4-flash", "messages": [{"role": "user", "content": "你好"}]}'
```

**解决**: 在对应平台重新获取有效的 API Key

### 9.4 模型文件缺失

**现象**: ASR 初始化失败，提示找不到模型

**错误日志**:
```
FileNotFoundError: models/SenseVoiceSmall/model.pt
```

**解决**:

```bash
# 下载模型
wget -O models/SenseVoiceSmall/model.pt \
  https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt

# 或使用百度网盘 (提取码: qvna)
# https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna
```

### 9.5 libopus/ffmpeg 缺失

**现象**: TTS 任务出错，文件不存在

**解决**:

```bash
# Conda 环境
conda install libopus -y
conda install ffmpeg -y

# Ubuntu/Debian
sudo apt install libopus-dev ffmpeg -y

# macOS
brew install opus ffmpeg
```

### 9.6 TTS 经常超时

**原因**: EdgeTTS 使用免费服务，可能不稳定

**解决**:

1. 检查是否使用代理，尝试关闭代理
2. 切换到付费 TTS 服务 (如火山引擎豆包 TTS)
3. 使用本地 TTS (MOSS-TTS)

### 9.7 语音识别语言错误

**现象**: 说话内容被识别为韩文/日文/英文

**原因**: SenseVoiceSmall 模型文件缺失，使用了备用模型

**解决**: 下载正确的模型文件到 `models/SenseVoiceSmall/model.pt`

---

## 10. 快速参考

### 10.1 最小配置模板

```yaml
# data/.config.yaml
server:
  websocket: ws://你的IP:8000/xiaozhi/v1/

selected_module:
  LLM: ChatGLMLLM

LLM:
  ChatGLMLLM:
    api_key: 你的智谱API密钥
```

### 10.2 目录结构

```
xiaozhi-esp32-server/
├── main/xiaozhi-server/
│   ├── app.py              # 主入口
│   ├── config.yaml         # 默认配置
│   ├── requirements.txt    # 依赖
│   ├── data/
│   │   └── .config.yaml    # 用户配置
│   ├── models/
│   │   ├── SenseVoiceSmall/
│   │   │   └── model.pt    # ASR 模型
│   │   └── snakers4_silero-vad/  # VAD 模型
│   └── tmp/                # 临时文件
```

### 10.3 常用命令

```bash
# 启动服务
python app.py

# 测试 WebSocket (需要 digital-human 模块)
# 浏览器访问 http://localhost:8000

# 检查服务状态
curl http://localhost:8003/xiaozhi/ota/
```

---

## 11. 相关文档

- [Deployment.md](./Deployment.md) - 官方部署指南
- [FAQ.md](./FAQ.md) - 常见问题
- [Deployment_all.md](./Deployment_all.md) - 全模块部署指南
