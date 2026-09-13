# Lingglot: real-time AI language video practice in Streamlit

This repository combines the supplied Lovable visual direction with the original Streamlit AI language-learning algorithms. It is implemented as a native Streamlit application and can be deployed directly from GitHub on Streamlit Community Cloud.

## Highlights

- Lovable-inspired cream, coral, pink, and magenta interface
- Home, Conversation, Video call, Mini-games, Progress, and About pages
- Real-time browser camera and microphone preview
- Continuous live speech transcript with interim words and finalized sentences
- Automatic transfer of each finalized sentence to the Python learning engine
- Luna's answer rendered and spoken in the selected target language
- Manual transcript fallback when browser speech recognition is unavailable
- Multilingual input guard for English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, and Arabic
- Reply-language guard that replaces a clearly wrong-language model answer with the correct localized fallback
- Adaptive difficulty, tutor feedback, rewards, learner clustering, mini-games, charts, and CSV export
- Optional local Hugging Face generation with `google/flan-t5-small`

## Conversation progress bar

The Conversation dashboard uses a Lovable-styled **Practice progress** bar instead of a Total points card. It fills from 0% to 100% toward a 100-point practice goal. Total points remain available on the Progress page and in exported history.

## Repository structure

```text
.
|-- streamlit_app.py
|-- lingglot/
|   |-- core.py
|   |-- language_detection.py
|   |-- realtime_call.py
|   |-- visuals.py
|   `-- __init__.py
|-- assets/
|   |-- styles.css
|   |-- logo-icon.svg
|   |-- logo-horizontal.svg
|   `-- characters/
|-- .streamlit/
|   `-- config.toml
|-- tests/
|-- docs/
|-- verify_repository.py
|-- requirements.txt
|-- requirements-full.txt
|-- requirements-dev.txt
`-- LICENSE
```

## Run locally

Python 3.12 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the HTTPS/local Streamlit address in a current Chromium-based browser, allow camera and microphone permission, then open **Video call**.

## Real-time video-call flow

1. Choose the target language and level.
2. Press **Start call** and allow camera and microphone access.
3. The `<video>` element displays the camera stream immediately in the browser.
4. Browser speech recognition shows interim words as the learner speaks.
5. Each finalized sentence is sent to Streamlit automatically.
6. The existing Python engine applies the multilingual guard, adaptive difficulty, feedback, points, and learner-profile updates.
7. Luna answers in the selected language; browser text-to-speech reads the answer aloud.
8. Recognition pauses while Luna speaks, then resumes for the next learner turn.

The camera stream is not recorded or intentionally uploaded by this application. Speech-recognition implementation and data handling depend on the browser. Chrome or Edge is recommended because support for continuous/interim Web Speech recognition varies across browsers. A manual transcript box remains available at all times.

This is an AI-character call, not a peer-to-peer human video meeting. Because the camera preview is local to the learner's browser, the default version does not need STUN or TURN credentials.

## Optional Hugging Face mode

Install the larger dependency set:

```bash
python -m pip install -r requirements-full.txt
streamlit run streamlit_app.py
```

Then enable **Local LLM**. The first use can download `google/flan-t5-small`, and the deployment needs enough memory for PyTorch and the model. The lightweight default deployment is recommended for Streamlit Community Cloud.

Regardless of model mode, the reply-language guard checks a generated reply and replaces a clear mismatch with Luna's localized fallback response.

## Deploy from GitHub to Streamlit Community Cloud

1. Extract the downloadable ZIP.
2. Upload or commit **all extracted contents** to the root of the GitHub repository. Do not upload only the ZIP file.
3. Confirm `streamlit_app.py`, `requirements.txt`, `lingglot/`, `assets/`, and `.streamlit/` are at the same repository level.
4. Run `python verify_repository.py` locally when possible.
5. In Streamlit Community Cloud, set the main file path to:

```text
streamlit_app.py
```

6. Deploy or reboot the app, open **Video call**, and grant camera/microphone permission in the browser address bar.

No secret is required for the default build. Never commit `.streamlit/secrets.toml`.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python verify_repository.py
python -m pytest -q
```

## Credits

- Author: Isabella Fu
- Mentor and advisor: Qingyang Xiao

This is a research and product prototype. Learner profiles and skill indicators are demonstrations, not standardized language-proficiency assessments.
