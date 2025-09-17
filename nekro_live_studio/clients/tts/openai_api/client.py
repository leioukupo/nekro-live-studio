import asyncio
import io
from typing import AsyncIterator, Literal, Optional

import httpx

from ....configs.config import config
from ....services.ffmpeg import play_audio_stream_with_ffplay
from ....utils.logger import logger
from .exceptions import OpenAiAPIError


class OpenAiAPIClient:
    """openai API 客户端"""

    def __init__(self):
        self.config = config.TTS
        self.base_url = self.config.HOST_AND_PORT

    async def speak(
        self,
        model : str,
        input: str,
        voice: str | None = None,
        started_event: Optional[asyncio.Event] = None,
        finished_event: Optional[asyncio.Event] = None,
        volume: Optional[float] = None,
        loudness_queue: Optional[asyncio.Queue[Optional[float]]] = None,
    ) -> bool:
        """
        从文本生成语音并流式播放
        """
        if not self.config.ENABLED:
            logger.debug("OpenAi API 已禁用.")
            return False

        try:
            stream_generator = self._generate_speech_stream(model,input, voice)
            return await play_audio_stream_with_ffplay(
                stream_generator,
                started_event=started_event,
                finished_event=finished_event,
                volume=volume,
                loudness_queue=loudness_queue,
            )
        except Exception as e:
            logger.error(f"语音生成或流式播放失败: {e}")
            return False

    async def _generate_speech_stream(
        self,
        model: str,
        input: str,
        voice: str | None = None,
    ) -> AsyncIterator[bytes]:
        """
        调用 Openai API 并以异步生成器形式返回音频流
        """
        model_name = self.config.SERVICE_NAME.lower()

        params = {
            "model": model_name,
            "input": input,
            "voice": voice or self.config.SPEAKER_ID,
            "speed": 0.8,
            "response_format": "wav",
            "streaming": "true",
        }
        print(f"回答是{input}")
        request_url = f"{self.base_url}/v1/audio/speech"
        try:
            async with (
                httpx.AsyncClient() as client,
                client.stream(
                    "POST",
                    request_url,
                    json=params,
                    timeout=3000,
                ) as response,
            ):
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            raise OpenAiAPIError(error_message=e.response.text, status_code=e.response.status_code) from e
        except Exception as e:
            logger.error(f"生成语音流时发生错误: {e}")
            raise OpenAiAPIError(error_message=str(e)) from e


openai_api_client = OpenAiAPIClient()
