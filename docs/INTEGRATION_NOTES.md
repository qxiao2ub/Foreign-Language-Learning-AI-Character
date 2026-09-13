# Integration notes

## Preserved learning functions

- `LearnerState` session model
- Prompt construction for conversation and tutor feedback
- Localized fallback replies
- Optional Hugging Face text generation
- Multilingual learner-input validation
- Mistake estimation and reward calculation
- Epsilon-greedy adaptive difficulty
- Synthetic learner-profile generation and KMeans clustering
- Vocabulary, role-play, sentence expansion, history, analytics, and CSV export

## Added in the real-time call revision

- Streamlit Components V2 browser component
- Live `getUserMedia` camera/microphone preview
- Continuous and interim browser speech recognition
- Automatic finalized-utterance events from JavaScript to Python
- Sentence-by-sentence conversation history
- Browser text-to-speech in each selected locale
- Recognition pause/resume around Luna's speech
- Manual transcript fallback
- Reply-language guard for optional model output
- Automated tests for media, transcription, TTS, serialization, and language enforcement

## Deliberate limitations

- Browser speech-recognition availability and accuracy differ by browser, language, operating system, and installed services.
- The default fallback is rule based and is not a full generative model.
- `google/flan-t5-small` is optional because model downloads and PyTorch can exceed hosted resource limits.
- This is an AI-character call with local self-view, not peer-to-peer person-to-person video conferencing.
- Skill scores and learner clusters are prototype indicators, not standardized proficiency results.
