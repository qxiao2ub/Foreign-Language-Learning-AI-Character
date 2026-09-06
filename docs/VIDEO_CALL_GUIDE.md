# Lingglot Video Call Guide

## What the new page does

The **Video call** page adds a live camera and microphone experience around Luna while reusing the existing Lingglot learning engine. It is designed for Streamlit Community Cloud and keeps the Lovable cream/coral/magenta visual system.

### Core flow

1. Choose a target language and call level.
2. Press **START** in the camera card and allow browser camera/microphone permissions.
3. Speak a sentence naturally while looking toward the camera.
4. Type the sentence you spoke into the live transcript box.
5. Luna runs the same multilingual language guard, adaptive bandit, AI/fallback response, tutor feedback, points, and learner clustering used by the Conversation page.
6. Press **Hear Luna** to hear the response with the browser's installed voice for the selected language.
7. Use the WebRTC camera/mic toggle controls or **STOP** to end the media stream.

## Why transcript entry remains explicit

The default public deployment has no required API key and no heavyweight speech recognition model. `st.audio_input` captures a 16 kHz speech-quality voice note for replay, but the typed transcript is what is scored. This keeps deployment stable and prevents silent calls to third-party transcription services.

## Streamlit Cloud networking

`streamlit-webrtc` needs HTTPS plus STUN/TURN connectivity for remote WebRTC. The repository ships a public Google STUN server configuration. Some restrictive NAT/firewall environments need TURN. Optional Streamlit secrets are supported:

```toml
TURN_URL = "turn:your-turn-host:3478"
TURN_USERNAME = "username"
TURN_CREDENTIAL = "credential"
```

Do not commit `.streamlit/secrets.toml` to GitHub.

## Dependency

The deployment pins:

```text
streamlit-webrtc==0.77.0
```

This release supports Streamlit 1.51+ and uses media dependencies with Python 3.14 wheels.
