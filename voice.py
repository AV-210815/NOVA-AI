"""Speech-to-text for the voice input feature, via a local Whisper model.

The whisper import and model load are deferred to first use (not module import
time) so that normal chat usage never pays the memory cost of loading it.
"""
import tempfile
from pathlib import Path

import config

_model = None


def get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model(config.WHISPER_MODEL)
    return _model


def transcribe_audio(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """Writes the recorded audio to a temp file and transcribes it.

    Whisper decodes the file via ffmpeg, so it accepts whatever format the
    browser's MediaRecorder produced (webm/opus by default) without needing to
    re-encode client-side.
    """
    model = get_model()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        result = model.transcribe(temp_path)
        return result["text"].strip()
    finally:
        Path(temp_path).unlink(missing_ok=True)
