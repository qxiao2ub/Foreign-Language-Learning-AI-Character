from __future__ import annotations

from lingglot.realtime_call import (
    REALTIME_CALL_HTML,
    REALTIME_CALL_JS,
    serialize_call_history,
    svg_data_uri,
)


def test_component_requests_live_camera_and_microphone():
    assert "navigator.mediaDevices.getUserMedia" in REALTIME_CALL_JS
    assert "video:" in REALTIME_CALL_JS
    assert "audio:" in REALTIME_CALL_JS
    assert 'video.srcObject = stream' in REALTIME_CALL_JS


def test_component_provides_interim_and_final_live_transcript():
    assert "SpeechRecognition || window.webkitSpeechRecognition" in REALTIME_CALL_JS
    assert "recognition.continuous = true" in REALTIME_CALL_JS
    assert "recognition.interimResults = true" in REALTIME_CALL_JS
    assert "result.isFinal" in REALTIME_CALL_JS
    assert 'setTriggerValue("utterance"' in REALTIME_CALL_JS
    assert "LIVE TRANSCRIPT" in REALTIME_CALL_HTML


def test_component_speaks_luna_reply_in_selected_locale():
    assert "SpeechSynthesisUtterance" in REALTIME_CALL_JS
    assert "utterance.lang = runtime.locale" in REALTIME_CALL_JS
    assert "window.speechSynthesis.speak" in REALTIME_CALL_JS


def test_history_serialization_keeps_safe_fields_and_limit():
    messages = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Hola", "private": "drop me"},
        {
            "role": "assistant",
            "content": "¡Muy bien!",
            "feedback": "Good work",
            "points": 8,
        },
    ]
    serialized = serialize_call_history(messages, limit=2)
    assert serialized == [
        {"role": "user", "content": "Hola", "feedback": "", "points": 0},
        {
            "role": "assistant",
            "content": "¡Muy bien!",
            "feedback": "Good work",
            "points": 8,
        },
    ]


def test_luna_svg_is_embedded_as_data_uri(tmp_path):
    svg = tmp_path / "avatar.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    uri = svg_data_uri(svg)
    assert uri.startswith("data:image/svg+xml;base64,")
