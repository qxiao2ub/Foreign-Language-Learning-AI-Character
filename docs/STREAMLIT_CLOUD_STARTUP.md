# Streamlit Cloud startup notes

This repository is configured for Streamlit Community Cloud with:

- `streamlit==1.58.0`
- no static-file serving requirement
- a 10-color sequential chart palette
- `streamlit_app.py` as the entrypoint

The Cloud log messages about PyArrow replacement are informational. The previous warnings about a missing `static/` folder and a five-color sequential palette have been removed.

## Deployment

Use:

```text
Main file path: streamlit_app.py
```

After pushing a new commit to GitHub, use **Manage app -> Reboot app** in Streamlit Cloud.
