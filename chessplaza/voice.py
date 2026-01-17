"""Voice/TTS support for Chess Plaza using edge-tts and miniaudio."""

import tempfile
import os
import time

# These are optional dependencies - only imported if --voice is used
_edge_tts = None
_miniaudio = None


def _load_voice_deps():
    """Lazy-load voice dependencies."""
    global _edge_tts, _miniaudio
    if _edge_tts is None:
        try:
            import edge_tts
            import miniaudio

            _edge_tts = edge_tts
            _miniaudio = miniaudio
        except ImportError:
            raise ImportError("Voice support requires extra dependencies. Install with: uv pip install -e '.[voice]'")


def is_voice_available() -> bool:
    """Check if voice dependencies are available."""
    try:
        _load_voice_deps()
        return True
    except ImportError:
        return False


async def speak(text: str, voice: str = "en-US-GuyNeural") -> None:
    """Generate speech from text and play it.

    Args:
        text: The text to speak (should be TTS-friendly, clean grammar)
        voice: The edge-tts voice ID to use
    """
    if not text or not text.strip():
        return

    _load_voice_deps()

    communicate = _edge_tts.Communicate(text, voice)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = f.name
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])

    try:
        _play_mp3_blocking(temp_path)
    finally:
        os.unlink(temp_path)


def _play_mp3_blocking(filepath: str) -> None:
    """Play an MP3 file and wait for completion."""
    _load_voice_deps()

    # Get actual duration from file
    info = _miniaudio.mp3_get_file_info(filepath)
    duration = info.duration

    stream = _miniaudio.stream_file(filepath)
    device = _miniaudio.PlaybackDevice()
    device.start(stream)

    # Wait for full duration plus buffer
    time.sleep(duration + 0.3)
    device.close()
