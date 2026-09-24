# Lingglot UI Revision — September 2026

This revision changes the learner-facing interface without removing the underlying learning engine.

## Conversation
- Compact character selector replaces the large character image.
- Difficulty is a dropdown labeled `Difficulty level`.
- New chat and Reset all are at the top of the chat area.
- Adaptive-difficulty and local-Hugging-Face controls are removed from the learner UI.
- The learner-facing labels for language/adaptive/fallback modes are removed.
- A compact Dictate button uses browser speech recognition and places captured text into the composer automatically.
- The white composer is widened and uses a cleaner row layout.
- Tutor feedback shows only the points earned.

## Video Call
- Character selector is shown above the call.
- Adaptive/local-LLM controls are removed from the learner UI.
- Finalized speech is automatically submitted; there is no review/type-a-sentence step.
- Character-specific ElevenLabs voice IDs can be configured through Streamlit Secrets.
- A computer-generated transcript is shown after/under the call and is built automatically from finalized utterances.

## Mini-games
- Removed the old Vocabulary quiz, Role-play, and Sentence expansion tabs from the learner UI.
- Added Word match, Listening challenge, and Word-to-picture match.
- The layout follows the supplied Lovable visual direction: warm cards, compact rounds, audio waveform/play treatment, and picture cards.

## Progress
- Removed Adaptive difficulty and Clustering model tabs.
- Removed CSV download from the learner UI.
- Replaced the scattered dashboard with a 100-point journey, skill snapshot, practice summary, and recent practice table.

## 100-point system note
The request referenced a separate detailed `100-point system revamping` section, but that section was not included in the supplied message. This revision therefore preserves the existing scoring algorithm and uses 100 as the learner-facing progress goal/cap rather than inventing new scoring weights.
