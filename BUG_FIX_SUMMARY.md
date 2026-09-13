# Real-time video and transcript revision

## Problems addressed

The previous Video call experience behaved more like a media recorder: the learner could not rely on a persistent live call view, speech was not transcribed continuously, and the learner had to enter the spoken sentence manually before Luna could respond.

## New implementation

- Live camera and microphone are opened with browser `getUserMedia`.
- The video element displays the current camera stream in real time.
- Web Speech recognition runs continuously with interim results enabled.
- Interim words are updated while the learner is speaking.
- Every finalized sentence is sent to Streamlit as a Components V2 trigger.
- The original AI/adaptive-learning pipeline processes each sentence.
- Luna's reply is shown, saved in the live transcript, and spoken in the selected target-language locale.
- Recognition pauses while Luna speaks and resumes afterward.
- A manual transcript fallback remains available for unsupported browsers.
- A reply-language guard replaces a clear wrong-language model response with the correct localized fallback.

## Verification

Run:

```bash
python verify_repository.py
python -m pytest -q
```
