from __future__ import annotations

import json
from dataclasses import dataclass, field
from uuid import uuid4

from starlette.websockets import WebSocket, WebSocketDisconnect

from voice_coach.boundaries import SpeechSynthesizer, Transcriber
from voice_coach.coach import VoiceCoach


@dataclass
class VoiceCoachSession:
    websocket: WebSocket
    transcriber: Transcriber
    synthesizer: SpeechSynthesizer
    coach: VoiceCoach
    max_audio_buffer_bytes: int
    session_id: str = field(default_factory=lambda: str(uuid4()))
    _audio_buffer: bytearray = field(default_factory=bytearray)

    async def run(self) -> None:
        await self.websocket.accept()
        await self._send_json({"type": "ready", "session_id": self.session_id})

        try:
            while True:
                message = await self.websocket.receive()
                if "bytes" in message and message["bytes"] is not None:
                    await self._buffer_audio(message["bytes"])
                    continue

                if "text" in message and message["text"] is not None:
                    should_continue = await self._handle_text_message(message["text"])
                    if not should_continue:
                        return
        except WebSocketDisconnect:
            return

    async def _buffer_audio(self, chunk: bytes) -> None:
        if not chunk:
            return
        if len(self._audio_buffer) + len(chunk) > self.max_audio_buffer_bytes:
            self._audio_buffer.clear()
            await self._send_json({"type": "error", "message": "audio buffer limit exceeded"})
            return
        self._audio_buffer.extend(chunk)
        await self._send_json({"type": "partial", "bytes": len(self._audio_buffer)})

    async def _handle_text_message(self, raw_message: str) -> bool:
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            await self._send_json({"type": "error", "message": "invalid json message"})
            return True

        message_type = message.get("type")
        if message_type == "close":
            await self.websocket.close()
            return False
        if message_type == "commit":
            await self._commit_audio(content_type=message.get("content_type", "audio/webm"))
            return True

        await self._send_json({"type": "error", "message": f"unsupported message type: {message_type}"})
        return True

    async def _commit_audio(self, *, content_type: str) -> None:
        if not self._audio_buffer:
            await self._send_json({"type": "error", "message": "no audio to commit"})
            return

        audio = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        transcript = await self.transcriber.transcribe(audio, content_type=content_type)
        await self._send_json({"type": "transcript", "text": transcript})

        coaching_text = await self.coach.respond(transcript)
        await self._send_json({"type": "coach", "text": coaching_text})

        async for audio_chunk in self.synthesizer.synthesize(coaching_text):
            await self.websocket.send_bytes(audio_chunk)

        await self._send_json({"type": "done"})

    async def _send_json(self, payload: dict[str, object]) -> None:
        await self.websocket.send_text(json.dumps(payload, separators=(",", ":")))
