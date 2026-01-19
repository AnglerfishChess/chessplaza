"""
GenAI Voice Prototype - TTS + STT dialog loop.

Tests Google GenAI for:
- Text-to-speech (gemini-2.5-flash-preview-tts)
- Speech-to-text (gemini-2.5-flash with audio input)
- Maintained dialog context

Usage:
    uv run python tests/proto/genai_voice.py

Requires GEMINI_API_KEY in .env file or environment.
"""

import base64
import io
import os
import tempfile
import time
import wave
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Check for API key
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    print("Error: Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
    print("Get one at: https://aistudio.google.com/apikey")
    exit(1)

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai not installed. Run: uv pip install google-genai")
    exit(1)

try:
    import miniaudio
except ImportError:
    print("Error: miniaudio not installed. Run: uv pip install miniaudio")
    exit(1)

# Selected capture device (set during startup)
selected_capture_device: Optional[dict] = None


def list_audio_devices() -> tuple[list[dict], list[dict]]:
    """List available audio devices. Returns (capture_devices, playback_devices)."""
    devices = miniaudio.Devices()
    return devices.get_captures(), devices.get_playbacks()


def select_capture_device() -> Optional[dict]:
    """Let user select a capture device. Returns device dict or None for default."""
    captures, playbacks = list_audio_devices()

    print("\n=== Audio Devices ===")
    print("\nCapture (input) devices:")
    if not captures:
        print("  (none found)")
    else:
        for i, dev in enumerate(captures):
            print(f"  [{i}] {dev['name']}")

    print("\nPlayback (output) devices:")
    if not playbacks:
        print("  (none found)")
    else:
        for i, dev in enumerate(playbacks):
            print(f"  [{i}] {dev['name']}")

    if not captures:
        print("\nNo capture devices found! Cannot record audio.")
        return None

    if len(captures) == 1:
        print(f"\nUsing: {captures[0]['name']}")
        return captures[0]

    # Multiple devices - let user choose
    print(f"\nSelect capture device [0-{len(captures) - 1}] or Enter for default: ", end="")
    choice = input().strip()
    if not choice:
        return captures[0]
    try:
        idx = int(choice)
        if 0 <= idx < len(captures):
            print(f"Using: {captures[idx]['name']}")
            return captures[idx]
    except ValueError:
        pass
    print(f"Invalid choice, using default: {captures[0]['name']}")
    return captures[0]


# Initialize client
client = genai.Client(api_key=API_KEY)

# Character configuration
CHARACTER_NAME = "Zara"
CHARACTER_VOICE = "Kore"  # One of the 30 Gemini TTS voices

# Director's Notes for TTS style control (Gemini TTS feature)
# Format: Prepend to text being spoken. Uses natural language style guidance.
# See: https://ai.google.dev/gemini-api/docs/speech-generation
DIRECTOR_NOTES = """### DIRECTOR'S NOTES
Style: Speak with a knowing, slightly world-weary tone. There should be warmth underneath the sarcasm.
Pacing: Measured, with slight pauses before witty remarks. Not rushed.
"""

# For the LLM prompt (personality/content generation)
CHARACTER_STYLE = "a witty space trader from the outer colonies, slightly sarcastic but friendly"

# Audio settings
# TTS outputs 24kHz, but STT works better with 16kHz (speech recognition standard)
TTS_SAMPLE_RATE = 24000
STT_SAMPLE_RATE = 16000

# Conversation history for context
conversation_history: list[dict[str, str]] = []


def text_to_speech(text: str, voice: str = CHARACTER_VOICE, director_notes: str = DIRECTOR_NOTES) -> bytes:
    """Convert text to speech using Gemini TTS. Returns PCM audio data.

    Args:
        text: The text to speak.
        voice: Voice name (one of 30 Gemini TTS prebuilt voices).
        director_notes: Style instructions prepended to text (Gemini TTS feature).
    """
    # Prepend director's notes for style control
    styled_text = f"{director_notes}\n{text}" if director_notes else text

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=styled_text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )

    # Extract base64-encoded PCM data
    audio_data = response.candidates[0].content.parts[0].inline_data.data

    # The data is already bytes (PCM), just return it
    if isinstance(audio_data, str):
        return base64.b64decode(audio_data)
    return audio_data


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw PCM to WAV format."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def play_audio(pcm_data: bytes, sample_rate: int = TTS_SAMPLE_RATE):
    """Play PCM audio using miniaudio."""
    wav_data = pcm_to_wav(pcm_data, sample_rate)

    # Write to temp file for miniaudio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_data)
        temp_path = f.name

    try:
        info = miniaudio.wav_get_file_info(temp_path)
        stream = miniaudio.stream_file(temp_path)
        device = miniaudio.PlaybackDevice()
        device.start(stream)
        time.sleep(info.duration + 0.3)
        device.close()
    finally:
        os.unlink(temp_path)


def record_audio(duration_seconds: float = 5.0, sample_rate: int = STT_SAMPLE_RATE) -> bytes:
    """Record audio from microphone. Returns PCM data.

    Args:
        duration_seconds: How long to record.
        sample_rate: Sample rate in Hz. 16kHz is standard for speech recognition.
    """
    global selected_capture_device
    device_id = selected_capture_device["id"] if selected_capture_device else None

    print(f"  [Recording for {duration_seconds}s... speak now!]")

    recorded_data = bytearray()

    # Create generator for capture
    def audio_generator():
        while True:
            data = yield
            if data:
                recorded_data.extend(data)

    gen = audio_generator()
    next(gen)  # Prime the generator

    capture = miniaudio.CaptureDevice(
        input_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=sample_rate,
        buffersize_msec=100,
        device_id=device_id,
    )
    capture.start(gen)
    time.sleep(duration_seconds)
    capture.stop()
    capture.close()

    print("  [Recording complete]")
    return bytes(recorded_data)


def speech_to_text(pcm_data: bytes, sample_rate: int = STT_SAMPLE_RATE) -> str:
    """Transcribe speech using Gemini.

    Args:
        pcm_data: Raw PCM audio (16-bit signed, mono).
        sample_rate: Sample rate in Hz. 16kHz is standard for speech recognition.
    """
    # Convert to WAV for upload
    wav_data = pcm_to_wav(pcm_data, sample_rate)

    # Upload as inline data with clear transcription prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="audio/wav",
                            data=wav_data,
                        )
                    ),
                    types.Part(
                        text="Listen to this audio recording and transcribe exactly what the person says. "
                        "If you cannot understand anything or the audio is silent, respond with: [inaudible]. "
                        "Otherwise, return only the spoken words, nothing else."
                    ),
                ]
            )
        ],
    )

    return response.text.strip()


def generate_response(user_input: str) -> str:
    """Generate character response using Gemini."""
    conversation_history.append({"role": "user", "content": user_input})

    # Build conversation context
    history_text = "\n".join(
        f"{'User' if msg['role'] == 'user' else CHARACTER_NAME}: {msg['content']}"
        for msg in conversation_history[-6:]  # Last 6 messages for context
    )

    prompt = f"""You are {CHARACTER_NAME}, {CHARACTER_STYLE}.

Previous conversation:
{history_text}

Respond to the user's last message in character. Keep your response to 1-2 sentences.
Do not include your name prefix in the response - just speak directly."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    assistant_response = response.text.strip()
    conversation_history.append({"role": "assistant", "content": assistant_response})

    return assistant_response


def say(text: str):
    """Have the character say something (print + TTS)."""
    print(f"\n{CHARACTER_NAME}: {text}")
    try:
        audio = text_to_speech(text)
        play_audio(audio)
    except Exception as e:
        print(f"  [TTS error: {e}]")


def main():
    """Main dialog loop."""
    global selected_capture_device

    print("\n=== GenAI Voice Prototype ===")
    print(f"Character: {CHARACTER_NAME} ({CHARACTER_STYLE})")
    print(f"Voice: {CHARACTER_VOICE}")

    # Select audio capture device
    selected_capture_device = select_capture_device()
    if selected_capture_device is None:
        print("Cannot continue without a capture device.")
        return

    print("\nPress Ctrl+C to exit\n")

    # Opening line
    opening = generate_response("[User just approached]")
    say(opening)

    while True:
        try:
            print("\n[Press Enter to speak, or type 'q' to quit]")
            user_choice = input("> ").strip().lower()

            if user_choice == "q":
                farewell = generate_response("[User is leaving]")
                say(farewell)
                break

            # Record and transcribe
            audio = record_audio(duration_seconds=5.0)

            # Debug: show audio stats
            expected_bytes = STT_SAMPLE_RATE * 2 * 5  # 16kHz * 2 bytes * 5 seconds
            print(f"  [Captured {len(audio)} bytes, expected ~{expected_bytes}]")

            if len(audio) < 1000:  # Too short, probably silence
                print("  [No audio detected, try again]")
                continue

            transcription = speech_to_text(audio)
            print(f"\nUser: {transcription}")

            if not transcription or transcription.lower() in ["", "none", "silence", "[inaudible]"]:
                print("  [Could not understand, try again]")
                continue

            # Generate and speak response
            response = generate_response(transcription)
            say(response)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue


if __name__ == "__main__":
    main()
