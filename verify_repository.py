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
    ROOT / "lingglot" / "__init__.py",
    ROOT / "lingglot" / "core.py",
    ROOT / "lingglot" / "language_detection.py",
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
    "lingglot.visuals",
):
    module = importlib.import_module(module_name)
    print(f"Imported {module_name} from {Path(module.__file__).relative_to(ROOT)}")

print("Repository check PASSED.")
