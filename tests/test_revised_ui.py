from pathlib import Path

from lingglot.dictation import HTML as DICTATION_HTML, JS as DICTATION_JS
from lingglot.realtime_call import REALTIME_CALL_HTML, REALTIME_CALL_JS


def test_dictation_component_is_present_and_emits_text():
    assert "Dictate" in DICTATION_HTML
    assert "SpeechRecognition" in DICTATION_JS
    assert "setTriggerValue" in DICTATION_JS
    assert "dictation" in DICTATION_JS


def test_realtime_call_has_no_manual_review_ui():
    assert "Review or type a sentence" not in REALTIME_CALL_HTML
    assert 'id="manual-transcript"' not in REALTIME_CALL_HTML
    assert 'submitUtterance(finalText, "speech")' in REALTIME_CALL_JS


def test_revision_source_contains_new_game_and_progress_labels():
    source = Path(__file__).parents[1].joinpath("streamlit_app.py").read_text()
    for label in ("Word match", "Listening challenge", "Word-to-picture"):
        assert label in source
    assert "Computer-generated transcript" in source
    assert "Difficulty level" in source
    assert "Use adaptive difficulty" not in source
    assert "Use local Hugging Face model" not in source
    assert "Adaptive level" not in source


def test_about_page_does_not_advertise_removed_controls():
    source = Path(__file__).parents[1].joinpath("streamlit_app.py").read_text()
    assert "CSV history download" not in source
