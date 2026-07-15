# Integration notes

## Preserved from the original Streamlit project

- `LearnerState` session model
- Prompt construction for conversation and tutor feedback
- Rule-based multilingual replies
- Optional Hugging Face text-to-text generation
- Chinese-character guard when English is selected
- Simple mistake estimation and reward calculation
- Epsilon-greedy difficulty bandit
- Synthetic learner-profile generation
- StandardScaler and KMeans learner clustering
- Vocabulary quiz, role-play prompt, and sentence expansion challenge
- Practice-history dataframe and CSV export

## Improvements made during integration

- Separated learning logic from the Streamlit UI for easier testing
- Replaced Streamlit-specific caching in the core with `functools.lru_cache`
- Added vocabulary banks for German, Italian, Portuguese, and Arabic so every selectable language has matching quiz content
- Prevented repeated point awards for the same vocabulary question
- Added a polished landing page and top navigation
- Added a two-column character/settings and chat workspace
- Added live visual skill indicators derived from session statistics
- Added self-contained SVG character and logo assets
- Added unit tests and deployment documentation

## Deliberate limitations

- The default conversation fallback is rule based and is not a full generative model.
- `google/flan-t5-small` is optional because PyTorch and model downloads can be too large for some hosted deployments.
- Skill scores and learner clusters are prototype indicators, not standardized proficiency scores.
- Speech recognition and text-to-speech are not part of the supplied algorithm ZIP and were not invented during this integration.
