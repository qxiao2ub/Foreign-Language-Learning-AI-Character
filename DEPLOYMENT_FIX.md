# Streamlit deployment structure

`lingglot` is a local package bundled with this repository. Do not add `lingglot` to `requirements.txt` as a third-party package.

The GitHub repository root must contain:

```text
streamlit_app.py
requirements.txt
lingglot/
  __init__.py
  core.py
  language_detection.py
  realtime_call.py
  visuals.py
assets/
.streamlit/
```

## Upload and deploy

1. Extract the downloadable ZIP.
2. Upload or commit every extracted file and folder to the GitHub repository root.
3. Do not store only the ZIP in GitHub; Streamlit does not unpack it.
4. Set the Streamlit Community Cloud main file path to `streamlit_app.py`.
5. Reboot the app after the new commit is visible.
6. Open the app in Chrome or Edge, allow camera and microphone permission, and test the Video call page.

Before pushing, run:

```bash
python verify_repository.py
```

A successful result ends with `Repository check PASSED.`
