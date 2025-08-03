# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Voice Agent web application that orchestrates a voice conversation pipeline through multiple AI services. It's built with Python Flask backend and vanilla JavaScript frontend with WebRTC audio processing.

## Architecture

The application follows a **microservices orchestration pattern** with a central Flask coordinator:

```
User Speech → Whisper (STT) → n8n Webhook (LLM) → Kokoro (TTS) → User Audio
```

**Core Components:**
- `main.py` - Flask application serving web interface and handling audio processing pipeline
- `templates/simple_agent.html` - Primary voice interface with advanced VAD and WebRTC audio handling
- External services: Whisper (STT), n8n webhook (LLM), Kokoro (TTS)

## Development Commands

**Environment Setup:**
```bash
# Activate virtual environment (required)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Running the Application:**
```bash
# Development server (default configuration)
python main.py
# Runs on http://0.0.0.0:5001 with debug=True
```

## Service Dependencies

The application integrates with external AI services on the local network:

- **Whisper Service**: `http://192.168.30.10:5050` - Speech-to-text transcription
- **Kokoro Service**: `http://192.168.30.10:8880` - Text-to-speech synthesis
- **n8n Webhook**: `https://noble-warthog-simply.ngrok-free.app/webhook/...` - LLM processing

These can be overridden via environment variables (WHISPER_URL, KOKORO_URL, etc.).

## Key Technical Details

**Audio Processing Pipeline:**
1. Browser captures microphone via WebRTC MediaRecorder
2. Voice Activity Detection (VAD) triggers recording start/stop
3. Audio sent to Flask `/process_audio` endpoint as FormData
4. Sequential processing through external services
5. Generated audio returned and streamed to browser

**Frontend Architecture:**
- Vanilla JavaScript with sophisticated WebRTC audio handling
- Real-time voice activity detection with configurable thresholds
- Barge-in capability (interrupt AI while speaking)
- Session management with UUID tracking
- CSS animations for visual state feedback

**Session Management:**
- Persistent conversation sessions using UUID
- Session state maintained in browser localStorage
- Audio context management for consistent playback

## Environment Configuration

The application uses a layered configuration approach with `python-dotenv`:
1. `.env.local` - Primary configuration file (git-ignored, environment-specific)
2. `.env` - Fallback configuration file (can be committed for defaults)

Copy `.env.local` and customize for your environment:

```bash
# Flask Configuration
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Service URLs
WHISPER_URL=http://192.168.30.10:5050
KOKORO_URL=http://192.168.30.10:8880
N8N_WEBHOOK_URL=https://your-webhook-url.ngrok-free.app/webhook/your-id

# Whisper Configuration
WHISPER_LANGUAGE=en

# Kokoro Configuration
KOKORO_MODEL=kokoro
KOKORO_VOICE=af_heart

# Audio Processing Configuration
SILENCE_THRESHOLD=-40
BARGE_IN_THRESHOLD=-30
SILENCE_DURATION=1000
SAMPLE_RATE=44100
```

The frontend automatically loads audio configuration from the `/config` endpoint.

## File Structure Notes

- `templates/simple_agent.html` is the primary interface used by main.py
- `templates/index.html` and `index.html` are alternative interfaces
- Single-file Flask application architecture in `main.py`
- No test infrastructure currently present