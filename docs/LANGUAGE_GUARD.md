# Multilingual target-language guard

## Bug fixed

The earlier implementation only rejected Chinese characters when **English**
was selected. Every other target-language combination bypassed validation.

## New behavior

The guard now covers all supported languages:

- English
- Spanish
- French
- German
- Italian
- Portuguese
- Chinese
- Japanese
- Korean
- Arabic

It combines:

1. Unicode-script recognition for Han, kana, Hangul, and Arabic writing.
2. Weighted common-word evidence for the six Latin-script languages.
3. Character accents and dependency-free character n-gram profiles.
4. Conservative confidence thresholds to avoid rejecting ambiguous input.

When a mismatch is clear, Luna:

- asks the learner—in the selected target language—to continue in that language;
- explains in English which language the message appears to use;
- awards zero points for that turn.

Examples:

| Selected target | Learner input | Result |
|---|---|---|
| Spanish | `Hello, how are you?` | Ask the learner in Spanish to practice Spanish |
| French | `Hallo, wie geht es dir?` | Ask the learner in French to practice French |
| Chinese | `こんにちは` | Ask the learner in Chinese to practice Chinese |
| Arabic | `你好` | Ask the learner in Arabic to practice Arabic |

Ambiguous words such as `pizza`, shared words such as `agua`, and ordinary
Japanese kanji-only text are not automatically rejected.
