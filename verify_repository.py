"""Verify that the repository has everything Streamlit needs before deploy."""

from __future__ import annotations

from pathlib import Path
import importlib
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED_PATHS = (
    ROOT / "streamlit_app.py",
    ROOT / "requirements.txt",
    ROOT / ".streamlit" / "config.toml",
    ROOT / "assets" / "styles.css",
    ROOT / "assets" / "characters" / "luna.svg",
    ROOT / "lingglot" / "__init__.py",
    ROOT / "lingglot" / "core.py",
    ROOT / "lingglot" / "language_detection.py",
    ROOT / "lingglot" / "realtime_call.py",
    ROOT / "lingglot" / "dictation.py",
    ROOT / "lingglot" / "elevenlabs_voice.py",
    ROOT / "lingglot" / "visuals.py",
)

missing = [path.relative_to(ROOT) for path in REQUIRED_PATHS if not path.is_file()]
if missing:
    print("Repository check FAILED. Missing:")
    for path in missing:
        print(f"  - {path}")
    raise SystemExit(1)

sys.path.insert(0, str(ROOT))
for module_name in (
    "lingglot",
    "lingglot.core",
    "lingglot.language_detection",
    "lingglot.realtime_call",
    "lingglot.dictation",
    "lingglot.elevenlabs_voice",
    "lingglot.visuals",
):
    module = importlib.import_module(module_name)
    print(f"Imported {module_name} from {Path(module.__file__).relative_to(ROOT)}")

from lingglot.realtime_call import REALTIME_CALL_JS  # noqa: E402

required_browser_features = (
    "navigator.mediaDevices.getUserMedia",
    "SpeechRecognition || window.webkitSpeechRecognition",
    "recognition.continuous = true",
    "recognition.interimResults = true",
    'setTriggerValue("utterance"',
    "window.speechSynthesis",
)
missing_features = [
    feature for feature in required_browser_features if feature not in REALTIME_CALL_JS
]
if missing_features:
    print("Repository check FAILED. Real-time component is incomplete:")
    for feature in missing_features:
        print(f"  - {feature}")
    raise SystemExit(1)

from lingglot.dictation import HTML as DICTATION_HTML, JS as DICTATION_JS  # noqa: E402
if "Dictate" not in DICTATION_HTML or "SpeechRecognition" not in DICTATION_JS or "setTriggerValue" not in DICTATION_JS:
    print("Repository check FAILED. Dictation component is incomplete.")
    raise SystemExit(1)
print("Conversation dictation component checks PASSED.")
print("Real-time video/transcript component checks PASSED.")
print("Repository check PASSED.")
