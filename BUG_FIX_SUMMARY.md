# Multilingual language-guard bug fix

## Problem

The previous implementation only handled this one mismatch:

- Target language: English
- Learner input: Chinese characters

Selecting Spanish, French, German, Italian, Portuguese, Chinese, Japanese,
Korean, or Arabic did not reliably reject input written in another supported
language.

## Fix

A new dependency-free module, `lingglot/language_detection.py`, now validates
all ten supported target languages. It uses Unicode scripts, weighted language
markers, accent evidence, and character n-gram profiles. Detection is
conservative so names, loanwords, and ambiguous short words are not rejected.

Mismatch responses are localized to the current target language. For example:

- Spanish target + English input: `Por favor, habla y practica en español.`
- French target + German input: `Parle et entraîne-toi en français, s’il te plaît.`
- Chinese target + Japanese input: `请用中文说话和练习。`
- Arabic target + Chinese input: `يرجى التحدث والتدرّب باللغة العربية.`

The tutor feedback also identifies the detected language and awards zero points
for the mismatched turn.

## Validation

The automated suite covers:

- detection of all ten supported languages;
- wrong-language rejection for every target language;
- acceptance of matching-language input for every target;
- ambiguous short words and shared Spanish/Portuguese words;
- Japanese kanji-only safeguards;
- zero-point behavior for rejected turns.

Run locally with:

```bash
python verify_repository.py
python -m pytest -q
```
