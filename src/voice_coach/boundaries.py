from __future__ import annotations

from io import BytesIO
from typing import AsyncIterator, Protocol


class Transcriber(Protocol):
    async def transcribe(self, audio: bytes, *, content_type: str = "audio/webm") -> str:
        """Return text for an audio payload."""


class SpeechSynthesizer(Protocol):
    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Yield encoded audio chunks for text."""


class WhisperTranscriber:
    def __init__(self, api_key: str, model: str) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - depends on deployment packaging
            raise RuntimeError("openai package is required for Whisper transcription") from exc

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def transcribe(self, audio: bytes, *, content_type: str = "audio/webm") -> str:
        filename = _filename_for_content_type(content_type)
        audio_file = BytesIO(audio)
        audio_file.name = filename
        result = await self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
            response_format="text",
        )
        return str(result).strip()


class CartesiaSpeechSynthesizer:
    def __init__(self, api_key: str, *, voice_id: str, model_id: str) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model_id = model_id

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        try:
            from cartesia import AsyncCartesia
        except ImportError as exc:  # pragma: no cover - depends on deployment packaging
            raise RuntimeError("cartesia package is required for TTS synthesis") from exc

        client = AsyncCartesia(api_key=self._api_key)
        stream = client.tts.bytes(
            model_id=self._model_id,
            transcript=text,
            voice={"mode": "id", "id": self._voice_id},
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 44100,
            },
        )
        async for chunk in stream:
            if chunk:
                yield bytes(chunk)


def _filename_for_content_type(content_type: str) -> str:
    suffix = {
        "audio/webm": "webm",
        "audio/wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp4": "mp4",
        "audio/ogg": "ogg",
    }.get(content_type, "webm")
    return f"speech.{suffix}"
