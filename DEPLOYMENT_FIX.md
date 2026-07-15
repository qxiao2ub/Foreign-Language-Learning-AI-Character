# Streamlit deployment fix

`lingglot` is a local Python package included in this repository. It is not a
third-party package that should be added to `requirements.txt`.

The following items must be at the same GitHub repository level:

```text
streamlit_app.py
requirements.txt
lingglot/
assets/
.streamlit/
```

Inside `lingglot/`, these files must exist:

```text
__init__.py
core.py
visuals.py
```

## Correct upload procedure

1. Extract the downloadable ZIP on your computer.
2. Open the extracted folder.
3. Upload or commit **all contents**, including the `lingglot`, `assets`, and
   `.streamlit` folders. Do not upload the ZIP file itself and expect GitHub or
   Streamlit to extract it.
4. In Streamlit Community Cloud, use `streamlit_app.py` as the main file path.
5. Reboot the app after the GitHub commit appears.

Run this before pushing:

```bash
python verify_repository.py
```

A successful result ends with:

```text
Repository check PASSED.
```
