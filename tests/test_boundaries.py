import sys
from io import BytesIO
from types import SimpleNamespace

from voice_coach.boundaries import WhisperTranscriber, _filename_for_content_type


def test_whisper_transcriber_calls_openai_boundary(monkeypatch):
    calls = {}

    class FakeTranscriptions:
        async def create(self, **kwargs):
            calls.update(kwargs)
            return " hello coach "

    class FakeAudio:
        transcriptions = FakeTranscriptions()

    class FakeClient:
        audio = FakeAudio()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=lambda api_key: FakeClient()))

    transcriber = WhisperTranscriber(api_key="test-key", model="whisper-test")
    import asyncio

    result = asyncio.run(transcriber.transcribe(b"abc", content_type="audio/wav"))

    assert result == "hello coach"
    assert calls["model"] == "whisper-test"
    assert calls["response_format"] == "text"
    assert isinstance(calls["file"], BytesIO)
    assert calls["file"].name == "speech.wav"


def test_filename_for_content_type_defaults_to_webm():
    assert _filename_for_content_type("application/octet-stream") == "speech.webm"
