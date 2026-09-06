# Lingglot: Lovable-styled Streamlit AI language app

This repository combines the supplied Lovable visual direction with the supplied Streamlit AI language-learning prototype.

The interface is implemented natively in Streamlit, so it can be deployed directly from GitHub on Streamlit Community Cloud. The React/Tailwind source is not embedded at runtime. Its visual system was translated into Streamlit theme configuration, CSS, responsive layouts, and lightweight SVG assets.


### Conversation progress bar

The Conversation dashboard replaces the former **Total points** summary card with a Lovable-styled **Practice progress** bar. The bar fills from 0% to 100% as the learner earns points toward a 100-point practice goal. Total points remain available on the dedicated Progress page and in exported practice history.

## What is included

- Lovable-inspired cream background, coral-to-magenta gradients, rounded cards, shadows, typography, phone mockup, and friendly character art
- Top navigation with Home, Conversation, Video call, Mini-games, Progress, and About pages
- AI character conversation with Luna
- Live WebRTC camera + microphone video-call practice with a Luna call stage
- Native voice-note capture plus browser text-to-speech for Luna replies
- Tutor feedback, rewards, and cumulative points
- Epsilon-greedy adaptive difficulty selection
- Scikit-learn learner-profile clustering
- Vocabulary, role-play, and sentence-expansion mini-games
- Session analytics and CSV history download
- Multilingual input guard for all 10 supported target languages, with localized correction prompts
- Optional local Hugging Face generation with `google/flan-t5-small`

## Repository structure

```text
.
|-- streamlit_app.py              # Streamlit entrypoint
|-- lingglot/
|   |-- core.py                    # AI, scoring, bandit, and clustering logic
|   |-- language_detection.py       # Multilingual script and language validation
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
|-- requirements.txt               # Streamlit + WebRTC deployment dependencies
|-- requirements-full.txt          # Optional local Hugging Face dependencies
|-- requirements-dev.txt
|-- LICENSE
`-- docs/
    |-- DESIGN_MAPPING.md
    |-- INTEGRATION_NOTES.md
    `-- VIDEO_CALL_GUIDE.md
```

## Run locally

Use Python 3.12-3.14. The pinned WebRTC release includes Python 3.14-compatible media dependencies.

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

## Video-call practice

Open **Video call** from the top navigation. The page combines:

- a large animated Luna call stage
- live browser camera and microphone through `streamlit-webrtc`
- camera and microphone toggle controls
- the same multilingual guard, adaptive difficulty, scoring, and learner profile used by Conversation
- a live-style transcript panel for submitting the sentence you spoke
- Streamlit's native 16 kHz voice-note recorder
- a **Hear Luna** control that uses the browser's speech-synthesis voice for the selected language

The default build intentionally avoids a required speech-to-text cloud API. The learner speaks naturally on camera, then types the sentence into the transcript box; this keeps the public Streamlit deployment key-free and predictable while preserving real camera/microphone interaction.

Remote WebRTC uses Google's public STUN server by default. On restrictive school, enterprise, or carrier networks a TURN relay may be required. If you have TURN credentials, add these Streamlit secrets without committing them to GitHub:

```toml
TURN_URL = "turn:your-turn-host:3478"
TURN_USERNAME = "your-username"
TURN_CREDENTIAL = "your-password-or-token"
```

Camera and microphone access also require browser permission and HTTPS. Streamlit Community Cloud provides HTTPS. Lingglot does not intentionally save the live WebRTC media stream.

## Multilingual target-language guard

The conversation page now validates input for every supported target language:
English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese,
Korean, and Arabic. The detector combines Unicode scripts with a lightweight
word and character n-gram model. Clear mismatches receive a localized request
to continue in the selected target language and earn zero points. Ambiguous
single words, names, loanwords, and shared Spanish/Portuguese vocabulary are
allowed rather than being rejected. No external language-detection package or
API key is required.

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
