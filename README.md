# Lingglot: Lovable-styled Streamlit AI language app

This repository combines the supplied Lovable visual direction with the supplied Streamlit AI language-learning prototype.

The interface is implemented natively in Streamlit, so it can be deployed directly from GitHub on Streamlit Community Cloud. The React/Tailwind source is not embedded at runtime. Its visual system was translated into Streamlit theme configuration, CSS, responsive layouts, and lightweight SVG assets.

## What is included

- Lovable-inspired cream background, coral-to-magenta gradients, rounded cards, shadows, typography, phone mockup, and friendly character art
- Top navigation with Home, Conversation, Mini-games, Progress, and About pages
- AI character conversation with Luna
- Tutor feedback, rewards, and cumulative points
- Epsilon-greedy adaptive difficulty selection
- Scikit-learn learner-profile clustering
- Vocabulary, role-play, and sentence-expansion mini-games
- Session analytics and CSV history download
- English-practice guard for Chinese input
- Optional local Hugging Face generation with `google/flan-t5-small`

## Repository structure

```text
.
|-- streamlit_app.py              # Streamlit entrypoint
|-- lingglot/
|   |-- core.py                    # AI, scoring, bandit, and clustering logic
|   |-- visuals.py                 # HTML and SVG visual helpers
|   `-- __init__.py
|-- assets/
|   |-- styles.css                 # Lovable-inspired visual system
|   |-- logo-icon.svg
|   |-- logo-horizontal.svg
|   `-- characters/
|-- .streamlit/
|   `-- config.toml                # Streamlit theme and server settings
|-- tests/
|   `-- test_core.py
|-- tools/
|   `-- generate_assets.py
|-- requirements.txt               # Lightweight deployment dependencies
|-- requirements-full.txt          # Optional local Hugging Face dependencies
|-- requirements-dev.txt
|-- LICENSE
`-- docs/
    |-- DESIGN_MAPPING.md
    `-- INTEGRATION_NOTES.md
```

## Run locally

Use Python 3.11 or 3.12 for the most predictable ML package compatibility.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The default app uses the built-in rule-based fallback and does not need an API key.

## Optional Hugging Face mode

Install the larger dependency set:

```bash
pip install -r requirements-full.txt
streamlit run streamlit_app.py
```

Then enable **Use local Hugging Face model** on the Conversation page. The first use may download `google/flan-t5-small`, and the deployment needs enough memory for PyTorch and the model.

For Streamlit Community Cloud, the lightweight `requirements.txt` is recommended. To deploy the full model mode, copy the additional packages from `requirements-full.txt` into `requirements.txt` and confirm the cloud resource limits are sufficient.

## Deploy from GitHub to Streamlit Community Cloud

1. Extract this ZIP. **Do not upload the ZIP file itself to GitHub and expect it to be unpacked.**
2. Create or clone your GitHub repository.
3. Upload or commit every item from the extracted repository root, including the `lingglot/`, `assets/`, and `.streamlit/` folders. The `lingglot/` folder must sit beside `streamlit_app.py`.
4. Before pushing, optionally run `python verify_repository.py`; it should print `Repository check PASSED.`
5. In Streamlit Community Cloud, create an app from the repository.
6. Set **Main file path** to:

```text
streamlit_app.py
```

7. Deploy. Streamlit installs `requirements.txt` automatically.

No secrets are required for the default configuration. Never commit `.streamlit/secrets.toml`.

## Run tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Design note

The original Lovable ZIP referenced a hosted logo asset through an `.asset.json` file but did not contain the PNG itself. This integrated repository therefore includes a new self-contained SVG speech-bubble logo using the same coral and magenta palette. The character art is recreated from the procedural SVG logic present in the Lovable source.

## Credits

- Author: Isabella Fu
- Mentor and advisor: Qingyang Xiao

This is a research and product prototype. The learner profile and skill indicators are demonstrations and are not formal language-proficiency assessments.
