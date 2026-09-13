"""Static validation for the real-time browser component JavaScript."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from lingglot.realtime_call import REALTIME_CALL_JS

REQUIRED_SNIPPETS = (
    "navigator.mediaDevices.getUserMedia",
    "recognition.continuous = true",
    "recognition.interimResults = true",
    "result.isFinal",
    'setTriggerValue("utterance"',
    "SpeechSynthesisUtterance",
    "video.srcObject = stream",
)

missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in REALTIME_CALL_JS]
if missing:
    raise SystemExit(f"Missing real-time component features: {missing}")

node = shutil.which("node")
if node:
    with tempfile.TemporaryDirectory() as directory:
        module_path = Path(directory) / "realtime_call.mjs"
        module_path.write_text(REALTIME_CALL_JS, encoding="utf-8")
        subprocess.run([node, "--check", str(module_path)], check=True)
    print("JavaScript syntax check PASSED.")
else:
    print("Node.js not installed; required feature checks PASSED.")
