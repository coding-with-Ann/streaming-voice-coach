from __future__ import annotations

from fastapi import Depends, FastAPI, WebSocket

from voice_coach.boundaries import CartesiaSpeechSynthesizer, WhisperTranscriber
from voice_coach.coach import VoiceCoach
from voice_coach.session import VoiceCoachSession
from voice_coach.settings import Settings, get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Streaming Voice Coach", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.websocket("/ws/coach")
    async def coach_socket(
        websocket: WebSocket,
        settings: Settings = Depends(get_settings),
    ) -> None:
        if not settings.openai_api_key or not settings.cartesia_api_key:
            await websocket.accept()
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "OPENAI_API_KEY and CARTESIA_API_KEY are required",
                }
            )
            await websocket.close(code=1011)
            return

        session = VoiceCoachSession(
            websocket=websocket,
            transcriber=WhisperTranscriber(
                api_key=settings.openai_api_key,
                model=settings.whisper_model,
            ),
            synthesizer=CartesiaSpeechSynthesizer(
                api_key=settings.cartesia_api_key,
                voice_id=settings.cartesia_voice_id,
                model_id=settings.cartesia_model_id,
            ),
            coach=VoiceCoach(),
            max_audio_buffer_bytes=settings.max_audio_buffer_bytes,
        )
        await session.run()

    return app


app = create_app()
