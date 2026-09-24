from __future__ import annotations

from lingglot.elevenlabs_voice import audio_data_uri, DEFAULT_MODEL_ID, DEFAULT_VOICE_ID


def test_audio_data_uri_is_browser_safe():
    uri = audio_data_uri(b"abc")
    assert uri == "data:audio/mpeg;base64,YWJj"


def test_defaults_match_optional_voice_configuration():
    assert DEFAULT_MODEL_ID == "eleven_flash_v2_5"
    assert DEFAULT_VOICE_ID


def test_realtime_component_has_elevenlabs_audio_support():
    from lingglot.realtime_call import REALTIME_CALL_JS
    assert "assistant_audio_data_uri" in REALTIME_CALL_JS
    assert "playElevenLabsAudio" in REALTIME_CALL_JS
    assert "speakAssistantWithFallback" in REALTIME_CALL_JS
