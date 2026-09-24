# Lingglot: real-time AI language video practice in Streamlit

This repository combines the supplied Lovable visual direction with the original Streamlit AI language-learning algorithms. It is implemented as a native Streamlit application and can be deployed directly from GitHub on Streamlit Community Cloud.

## Highlights

- Lovable-inspired cream, coral, pink, and magenta interface
- Compact character selector and difficulty controls in Conversation and Video call
- Conversation dictation button beside the composer
- Home, Conversation, Video call, Mini-games, Progress, and About pages
- Real-time browser camera and microphone preview
- Continuous live speech transcript with interim words and finalized sentences
- Automatic transfer of each finalized sentence to the Python learning engine
- Luna's answer rendered and spoken in the selected target language
- Automatic speech processing in Video call; no review/type step
- Multilingual input guard for English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, and Arabic
- Reply-language guard that replaces a clearly wrong-language model answer with the correct localized fallback
- Tutor feedback and rewards with a learner-friendly 100-point journey
- Character selection across six AI partners

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
8. Recognition pauses while the AI speaks, then resumes for the next learner turn.

The camera stream is not recorded or intentionally uploaded by this application. Speech-recognition implementation and data handling depend on the browser. Chrome or Edge is recommended because support for continuous/interim Web Speech recognition varies across browsers. Finalized speech is automatically submitted to the Python learning engine.

This is an AI-character call, not a peer-to-peer human video meeting. Because the camera preview is local to the learner's browser, the default version does not need STUN or TURN credentials.

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

## Optional natural Luna voice with ElevenLabs

The Video call experience can use ElevenLabs Text-to-Speech for natural AI replies. The default model is `eleven_flash_v2_5` for lower conversational latency, with `eleven_v3` available as an override. Add `ELEVENLABS_API_KEY` and optionally `ELEVENLABS_VOICE_ID` / `ELEVENLABS_MODEL_ID` to Streamlit Secrets. Without these secrets, the app falls back to browser speech synthesis. The integration follows ElevenLabs' current Text-to-Speech API pattern. See `docs/ELEVENLABS_VOICE.md`.


## UI revision (September 2026)

- Conversation uses a compact character selector, difficulty dropdown, top-level New chat/Reset all controls, a 100-point progress bar, and a dictation button beside the composer.
- Video Call removes adaptive/local-LLM settings, automatically processes finalized transcript sentences, adds character selection, and shows a computer-generated end transcript.
- Mini-games now focus on Word Match, Listening Challenge, and Word-to-Picture Match.
- Progress is simplified into a 100-point journey and recent practice snapshot; CSV export and model diagnostics are intentionally hidden from the learner-facing UI.
- The detailed 100-point scoring rules were not supplied in the revision request, so the existing scoring logic is preserved and the learner-facing goal is normalized to 100 points.


## UI revision — September 2026

The learner-facing UI now hides implementation controls such as adaptive-difficulty switches and local-model toggles. Those algorithms remain available in the Python core for prototype research but are not exposed as learner settings. The Mini-games page contains Word Match, Listening Challenge, and Word-to-Picture Match. The Progress page focuses on the 100-point journey, four skill indicators, a practice summary, and recent practice instead of model diagnostics or CSV export.

The revision request referenced detailed `100-point system revamping` rules, but the detailed rules were not included in the supplied message. The repository therefore preserves the existing scoring algorithm and uses 100 as the learner-facing goal until exact new scoring weights are supplied.
