# Streaming Voice Coach

A production-ready Python skeleton for a low-latency streaming voice AI coach.

The app exposes a WebSocket endpoint that accepts streamed microphone audio, buffers short chunks for transcription through a Whisper boundary, produces a coaching response, and streams synthesized speech frames back through a Cartesia TTS boundary.

## Features

- FastAPI WebSocket endpoint for bidirectional audio streaming.
- Explicit OpenAI Whisper API boundary for transcription.
- Explicit Cartesia TTS SDK boundary for speech synthesis.
- Dependency-injected service layer for fast tests and clean network mocking.
- Structured JSON control messages plus binary audio frames.
- Standard `tests/` suite with mocked WebSocket, OpenAI, and Cartesia boundaries.

## Protocol

Client to server:

- Binary frames: raw audio bytes.
- JSON text message: `{"type": "commit"}` to transcribe the current buffer.
- JSON text message: `{"type": "close"}` to end the session.

Server to client:

- `{"type": "ready", "session_id": "..."}`
- `{"type": "partial", "bytes": 1234}` when audio is buffered.
- `{"type": "transcript", "text": "..."}`
- `{"type": "coach", "text": "..."}`
- Binary frames containing synthesized audio chunks.
- `{"type": "done"}`
- `{"type": "error", "message": "..."}`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create environment variables for real network integrations:

```powershell
$env:OPENAI_API_KEY="..."
$env:CARTESIA_API_KEY="..."
```

## Run

```powershell
uvicorn voice_coach.app:create_app --factory --host 0.0.0.0 --port 8000
```

WebSocket URL:

```text
ws://localhost:8000/ws/coach
```

## Test

```powershell
pytest
```

Tests mock all network boundaries and do not require API keys.
