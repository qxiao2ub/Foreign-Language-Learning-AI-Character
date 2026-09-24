"""Optional ElevenLabs voice synthesis for Lingglot.

The API key is read from Streamlit secrets or the environment. No credentials
are stored in the repository. When ElevenLabs is not configured or fails, the
app can fall back to the browser's built-in speech synthesis.
"""
from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st


DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # ElevenLabs quickstart voice example.
DEFAULT_MODEL_ID = "eleven_flash_v2_5"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


def _secret_or_env(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value or os.getenv(name, default) or "").strip()


def elevenlabs_configured() -> bool:
    """Return True when an API key is available."""
    return bool(_secret_or_env("ELEVENLABS_API_KEY"))


def get_voice_id() -> str:
    """Return the configured ElevenLabs voice ID."""
    return _secret_or_env("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)


def get_model_id() -> str:
    """Return the configured ElevenLabs model ID."""
    return _secret_or_env("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID)


def synthesize_elevenlabs(text: str, *, language_code: str | None = None, timeout: float = 30.0) -> bytes:
    """Generate MP3 bytes using ElevenLabs Text-to-Speech."""
    text = str(text or "").strip()
    api_key = _secret_or_env("ELEVENLABS_API_KEY")
    if not text:
        raise ValueError("Text is empty.")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured.")

    voice_id = get_voice_id()
    model_id = get_model_id()
    output_format = _secret_or_env("ELEVENLABS_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)

    url = (
        "https://api.elevenlabs.io/v1/text-to-speech/"
        f"{voice_id}?output_format={output_format}"
    )
    payload_dict = {
        "text": text,
        "model_id": model_id,
    }
    if language_code:
        payload_dict["language_code"] = language_code.split("-")[0].lower()
    payload = json.dumps(payload_dict).encode("utf-8")

    request = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "User-Agent": "Lingglot/1.0",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            audio = response.read()
    except HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"ElevenLabs network error: {exc.reason}") from exc

    if not audio:
        raise RuntimeError("ElevenLabs returned an empty audio response.")
    return audio


def audio_data_uri(audio_bytes: bytes, mime_type: str = "audio/mpeg") -> str:
    """Convert audio bytes to a browser-safe data URI."""
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
