from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()  # Load .env as fallback

app = Flask(__name__)

# Flask Configuration
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

# Service URLs
WHISPER_URL = os.getenv("WHISPER_URL", "http://192.168.30.10:5050")
KOKORO_URL = os.getenv("KOKORO_URL", "http://192.168.30.10:8880")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://noble-warthog-simply.ngrok-free.app/webhook/0bd8d7d9-ef86-4258-a3c8-952f281ac4b3")

# Whisper Configuration
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

# Kokoro Configuration
KOKORO_MODEL = os.getenv("KOKORO_MODEL", "kokoro")
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")

# Audio Processing Configuration
AUDIO_CONFIG = {
    "SILENCE_THRESHOLD": int(os.getenv("SILENCE_THRESHOLD", "-40")),
    "BARGE_IN_THRESHOLD": int(os.getenv("BARGE_IN_THRESHOLD", "-30")),
    "SILENCE_DURATION": int(os.getenv("SILENCE_DURATION", "1000")),
    "SAMPLE_RATE": int(os.getenv("SAMPLE_RATE", "44100"))
}

@app.route('/')
def index():
    return render_template('simple_agent.html', audio_config=AUDIO_CONFIG)

@app.route('/config')
def config():
    """Endpoint to provide client-side configuration"""
    return jsonify(AUDIO_CONFIG)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    session_id = request.form.get('session_id', 'no_session_id')
    
    # 1. Send to Whisper for transcription
    try:
        whisper_response = requests.post(f"{WHISPER_URL}/transcribe", 
                                         files={"audio": (audio_file.filename, audio_file.stream, audio_file.mimetype)},
                                         data={"language": WHISPER_LANGUAGE})
        whisper_response.raise_for_status()
        transcription = whisper_response.json().get("text")
        print(f"Transcription: {transcription}")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Whisper service error: {e}"}), 500

    if not transcription:
        return jsonify({"error": "Could not transcribe audio"}), 500

    # 2. Send to n8n webhook for LLM processing
    try:
        webhook_payload = {
            "user_input": transcription,
            "session_id": session_id
        }
        webhook_response = requests.post(N8N_WEBHOOK_URL, json=webhook_payload)
        webhook_response.raise_for_status()
        # Assuming n8n returns a JSON with a 'response' key
        llm_response_text = webhook_response.json().get("response")
        print(f"LLM Response from n8n: {llm_response_text}")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"n8n webhook error: {e}"}), 500

    if not llm_response_text:
        return jsonify({"error": "Could not get response from LLM"}), 500

    # 3. Send to Kokoro for audio generation
    try:
        kokoro_payload = {
            "model": KOKORO_MODEL,
            "voice": KOKORO_VOICE,
            "input": llm_response_text
        }
        kokoro_response = requests.post(f"{KOKORO_URL}/v1/audio/speech", json=kokoro_payload)
        kokoro_response.raise_for_status()
        
        # Return audio directly
        return jsonify({
            "audio_data": list(kokoro_response.content),
            "transcription": transcription,
            "llm_response": llm_response_text
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Kokoro service error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
