# Lingglot Real-Time Video Call Guide

## What changed

The Video call page now uses a browser-native Streamlit Components V2 interface instead of a recording-style workflow. It keeps the camera preview and live speech-recognition session running in the browser while Streamlit processes finalized learner sentences.

## Call workflow

1. Select a target language and level.
2. Press **Start call**.
3. Grant camera and microphone permission.
4. The learner sees a live mirrored camera preview immediately.
5. Interim recognition text appears word by word in **Listening now**.
6. When the browser marks an utterance final, the sentence is added to the live transcript and sent to Python.
7. The Python engine validates the learner language, selects/adapts difficulty, generates feedback, awards points, and produces Luna's answer.
8. Luna's answer appears in the transcript and is spoken using the browser voice for the selected target locale.
9. Recognition pauses while Luna speaks and resumes afterward to prevent the AI voice from being transcribed as learner speech.

## Browser behavior

The component uses:

- `navigator.mediaDevices.getUserMedia()` for live camera and microphone access;
- `SpeechRecognition` or `webkitSpeechRecognition` for interim/final transcript events;
- `speechSynthesis` for Luna's spoken answer.

Camera and microphone access require a secure context and explicit user permission. Streamlit Community Cloud is served over HTTPS. Chrome or Edge is recommended because Web Speech recognition support is not uniform across browsers.

When live recognition is unsupported or temporarily fails, the live video remains available and the learner can type or correct a sentence in the automatic transcript panel.

## Privacy behavior

- Lingglot does not intentionally record or save the live camera stream.
- Only finalized transcript text is sent to the Python learning engine.
- Interim words remain inside the browser component.
- A browser may implement speech recognition with an online service; users should follow the browser/vendor privacy policy.

## Network behavior

This is an AI-character practice call with a local self-view, not a peer-to-peer human meeting. It therefore does not require STUN or TURN configuration in the default build.


### Current learner flow
- Choose character, target language, and difficulty level.
- Start the call and allow camera/microphone access.
- Finalized speech is submitted automatically; there is no manual review step.
- The selected character's ElevenLabs voice is used when configured through Streamlit Secrets.
- A computer-generated transcript is shown below the call stage.
