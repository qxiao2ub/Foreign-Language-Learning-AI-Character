# ElevenLabs natural voice for Luna

The Video call page supports optional ElevenLabs Text-to-Speech for more natural AI replies. The app remains deployable without ElevenLabs; it falls back to browser speech synthesis.

## Streamlit Cloud setup

In **App settings -> Secrets**, add:

```toml
ELEVENLABS_API_KEY = "your-elevenlabs-api-key"
ELEVENLABS_VOICE_ID = "your-voice-id"
ELEVENLABS_MODEL_ID = "eleven_v3"
```

`ELEVENLABS_VOICE_ID` is optional and defaults to the voice ID shown in ElevenLabs' current quickstart example. For a dedicated Luna character voice, create/select a voice in the ElevenLabs Voice Library and set its ID as the secret.

The key is never stored in this GitHub repository. The code calls the ElevenLabs Text-to-Speech API from the Streamlit server and sends only the generated audio back to the browser component. ElevenLabs documents the API-key secret pattern, the Python SDK, the `eleven_v3` model example, and the `voice_id` parameter in its quickstart. See https://elevenlabs.io/docs/eleven-api/quickstart

## Recommended architecture

```text
Browser camera + microphone
          |
          v
Live SpeechRecognition transcript
          |
          v
Streamlit + Lingglot AI engine
          |
          +----> ElevenLabs TTS (optional)
          |              |
          |              v
          |          MP3 audio
          |              |
          +--------------+
                         v
                  Luna speaks in browser
```

The current implementation keeps browser speech recognition for low-latency live interim transcript and uses ElevenLabs only for the AI reply audio. This avoids replacing the existing real-time camera/transcript component.

## Cost/privacy note

Each generated ElevenLabs reply is an API call and may consume ElevenLabs quota/credits according to the account plan. Do not put the API key in `requirements.txt`, JavaScript, or GitHub source files.

### Model choice

The default is `eleven_flash_v2_5` because ElevenLabs recommends Flash v2.5 for conversational, low-latency use. `eleven_v3` is more expressive, but ElevenLabs documents higher latency and says it is not suitable for real-time conversational use. You can override `ELEVENLABS_MODEL_ID` in Streamlit Secrets when you prefer expressiveness over latency.
