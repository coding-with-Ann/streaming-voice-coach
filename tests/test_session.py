import json
import asyncio

from voice_coach.coach import VoiceCoach
from voice_coach.session import VoiceCoachSession


class FakeWebSocket:
    def __init__(self, incoming):
        self.incoming = list(incoming)
        self.sent_text = []
        self.sent_bytes = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive(self):
        if not self.incoming:
            return {"text": json.dumps({"type": "close"})}
        return self.incoming.pop(0)

    async def send_text(self, message):
        self.sent_text.append(json.loads(message))

    async def send_bytes(self, message):
        self.sent_bytes.append(message)

    async def close(self, code=1000):
        self.closed = True
        self.close_code = code


class FakeTranscriber:
    def __init__(self):
        self.calls = []

    async def transcribe(self, audio, *, content_type="audio/webm"):
        self.calls.append((audio, content_type))
        return "Hello audience"


class FakeSynthesizer:
    def __init__(self):
        self.calls = []

    async def synthesize(self, text):
        self.calls.append(text)
        yield b"audio-1"
        yield b"audio-2"


def test_session_streams_transcript_coaching_and_tts():
    websocket = FakeWebSocket(
        [
            {"bytes": b"abc"},
            {"bytes": b"def"},
            {"text": json.dumps({"type": "commit", "content_type": "audio/wav"})},
            {"text": json.dumps({"type": "close"})},
        ]
    )
    transcriber = FakeTranscriber()
    synthesizer = FakeSynthesizer()
    session = VoiceCoachSession(
        websocket=websocket,
        transcriber=transcriber,
        synthesizer=synthesizer,
        coach=VoiceCoach(),
        max_audio_buffer_bytes=1024,
    )

    asyncio.run(session.run())

    assert websocket.accepted is True
    assert transcriber.calls == [(b"abcdef", "audio/wav")]
    assert websocket.sent_bytes == [b"audio-1", b"audio-2"]
    assert [message["type"] for message in websocket.sent_text] == [
        "ready",
        "partial",
        "partial",
        "transcript",
        "coach",
        "done",
    ]
    assert websocket.closed is True


def test_session_rejects_oversized_audio_buffer():
    websocket = FakeWebSocket([{"bytes": b"too-large"}, {"text": json.dumps({"type": "close"})}])
    session = VoiceCoachSession(
        websocket=websocket,
        transcriber=FakeTranscriber(),
        synthesizer=FakeSynthesizer(),
        coach=VoiceCoach(),
        max_audio_buffer_bytes=3,
    )

    asyncio.run(session.run())

    assert {"type": "error", "message": "audio buffer limit exceeded"} in websocket.sent_text
