import os
import base64
import time
import aiohttp
from datetime import datetime
from config.logger import setup_logging
from core.providers.tts.base import TTSProviderBase

TAG = __name__
logger = setup_logging()

# 内置音色列表
BUILTIN_VOICES = {"Junhao", "Xiaoyu", "Yuewen", "Xiaochen", "Xiaomeng", "Xiaorou"}


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.server_url = config.get("server_url", "http://localhost:18083")
        self.voice = config.get("voice", "Junhao")
        self.prompt_audio = config.get("prompt_audio")  # 自定义音色的参考音频路径
        self.audio_file_type = "wav"

    def generate_filename(self, extension=".wav"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{datetime.now().strftime('%H%M%S')}_{os.urandom(4).hex()}{extension}",
        )

    async def text_to_speak(self, text, output_file):
        tts_start = time.time()
        try:
            # 每次调用读取最新的 self.voice 值，支持运行时修改
            voice = self.voice

            # 判断是否使用内置音色
            if voice in BUILTIN_VOICES and not self.prompt_audio:
                # 内置音色走 /api/generate
                audio_bytes = await self._generate_builtin(text, voice)
            else:
                # 自定义音色走 /api/generate-with-reference
                audio_bytes = await self._generate_with_reference(text)

            logger.bind(tag=TAG).info(
                f"[耗时] TTS生成: {time.time() - tts_start:.3f}s | 文本长度: {len(text)}"
            )

            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
            else:
                return audio_bytes

        except Exception as e:
            error_msg = f"MOSS-TTS请求失败: {e}"
            raise Exception(error_msg)

    async def _generate_builtin(self, text, voice):
        """使用内置音色生成语音"""
        url = f"{self.server_url}/api/generate"
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("text", text)
            data.add_field("voice", voice)
            # 方案A：请求服务端重采样到 ESP32 目标采样率，避免客户端重采样引入失真
            if self.conn and hasattr(self.conn, 'sample_rate'):
                data.add_field("target_sample_rate", str(self.conn.sample_rate))

            async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=self.tts_timeout)) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}: {await resp.text()}")
                result = await resp.json()
                audio_base64 = result.get("audio_base64")
                if not audio_base64:
                    raise Exception("响应缺少 audio_base64")
                return base64.b64decode(audio_base64)

    async def _generate_with_reference(self, text):
        """使用自定义音色（参考音频）生成语音"""
        url = f"{self.server_url}/api/generate-with-reference"
        prompt_audio = self.prompt_audio

        if not prompt_audio or not os.path.exists(prompt_audio):
            raise Exception(f"参考音频不存在: {prompt_audio}")

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("text", text)
            # 方案A：请求服务端重采样到 ESP32 目标采样率
            if self.conn and hasattr(self.conn, 'sample_rate'):
                data.add_field("target_sample_rate", str(self.conn.sample_rate))
            with open(prompt_audio, "rb") as f:
                data.add_field("prompt_audio", f, filename=os.path.basename(prompt_audio))

            async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=self.tts_timeout)) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}: {await resp.text()}")
                result = await resp.json()
                audio_base64 = result.get("audio_base64")
                if not audio_base64:
                    raise Exception("响应缺少 audio_base64")
                return base64.b64decode(audio_base64)
