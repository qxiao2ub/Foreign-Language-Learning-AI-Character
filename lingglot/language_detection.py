"""Lightweight multilingual input validation for Lingglot.

The detector intentionally avoids a large external language-model dependency.
It combines Unicode-script detection with language-specific words, characters,
and character n-gram profiles for the six supported Latin-script languages.
Uncertain or very short ambiguous inputs are allowed instead of being blocked.
"""

from __future__ import annotations

from collections import Counter
import math
import re
import unicodedata
from typing import Dict, Optional, Tuple

LATIN_LANGUAGES = (
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
)

NON_LATIN_LANGUAGES = ("Chinese", "Japanese", "Korean", "Arabic")

# Frequent words and beginner-level vocabulary provide strong evidence for
# short messages, while shared words receive less weight automatically.
_LANGUAGE_WORD_MARKERS: Dict[str, set[str]] = {
    "English": set(
        """
        a the and is are am i you he she we they my your this that it to of in
        for with on at from hello hi thanks thank please good morning how what
        where when why because like want learn learning speak speaking today
        name can do have water friend school language english yes no
        """.split()
    ),
    "Spanish": set(
        """
        el la los las un una unos unas y es soy eres esta está estoy tu tú
        usted yo mi mis tus de del en para por con que hola gracias favor
        buenos dias días como cómo qué donde dónde cuando cuándo porque gusta
        quiero aprender hablar hoy llamo me muy bien puedo puede agua amigo
        escuela idioma español si sí no mañana mercado
        """.split()
    ),
    "French": set(
        """
        le la les un une des et est suis es êtes je tu vous il elle nous mon
        ma mes ton ta de du dans pour avec que bonjour salut merci plaît bon
        matin comment quoi où quand parce aime veux apprendre parler
        aujourd'hui appelle me très bien peux peut eau ami école langue
        français oui non demain marché au aux
        """.split()
    ),
    "German": set(
        """
        der die das den dem ein eine und ist bin bist sind ich du sie wir mein
        meine dein von im in für mit dass hallo danke bitte guten morgen wie
        was wo wann weil mag möchte lernen sprechen heute heiße heisse mich
        sehr gut kann kannst wasser freund schule sprache deutsch ja nein zum
        zur gehen
        """.split()
    ),
    "Italian": set(
        """
        il lo la i gli le un uno una e è sono sei io tu lei noi mio mia miei
        tuoi di del della in per con che ciao buongiorno grazie prego come cosa
        dove quando perché piace voglio imparare parlare oggi chiamo mi molto
        bene posso puoi acqua amico scuola lingua italiano sì si no domani al
        mercato
        """.split()
    ),
    "Portuguese": set(
        """
        o a os as um uma uns umas e é sou está estou eu você voce tu nós nos
        meu minha meus minhas de do da em para por com que olá ola oi obrigado
        obrigada favor bom dia como quê onde quando porque gosto quero aprender
        falar hoje chamo me muito bem posso pode agua água amigo escola idioma
        português portugues sim não nao amanhã amanha ao mercado
        """.split()
    ),
}

# Representative text supplies a dependency-free n-gram profile for messages
# that contain few explicit marker words.
_LANGUAGE_PROFILE_TEXT: Dict[str, str] = {
    "English": (
        "Hello, my name is Luna. I enjoy learning languages and speaking with "
        "my friends. Today I want to practice English because conversation "
        "helps me improve. How are you and what would you like to discuss? "
        "Tomorrow we can visit the market and talk about the weather."
    ),
    "Spanish": (
        "Hola, me llamo Luna. Me gusta aprender idiomas y hablar con mis "
        "amigos. Hoy quiero practicar español porque la conversación me ayuda "
        "a mejorar. ¿Cómo estás y de qué te gustaría hablar? Mañana iremos al "
        "mercado y hablaremos del tiempo."
    ),
    "French": (
        "Bonjour, je m'appelle Luna. J'aime apprendre les langues et parler "
        "avec mes amis. Aujourd'hui je veux pratiquer le français parce que la "
        "conversation m'aide à progresser. Comment vas-tu et de quoi veux-tu "
        "parler ? Demain nous irons au marché."
    ),
    "German": (
        "Hallo, ich heiße Luna. Ich lerne gern Sprachen und spreche mit meinen "
        "Freunden. Heute möchte ich Deutsch üben, weil Gespräche mir helfen. "
        "Wie geht es dir und worüber möchtest du sprechen? Morgen gehen wir "
        "zum Markt und reden über das Wetter."
    ),
    "Italian": (
        "Ciao, mi chiamo Luna. Mi piace imparare le lingue e parlare con i "
        "miei amici. Oggi voglio praticare l'italiano perché la conversazione "
        "mi aiuta a migliorare. Come stai e di cosa vuoi parlare? Domani "
        "andremo al mercato e parleremo del tempo."
    ),
    "Portuguese": (
        "Olá, eu me chamo Luna. Gosto de aprender idiomas e falar com meus "
        "amigos. Hoje quero praticar português porque a conversa me ajuda a "
        "melhorar. Como você está e sobre o que gostaria de falar? Amanhã "
        "iremos ao mercado e falaremos sobre o tempo."
    ),
}

_LANGUAGE_CHARACTER_HINTS: Dict[str, set[str]] = {
    "English": set(),
    "Spanish": set("ñ¿¡"),
    "French": set("àâæçéèêëîïôœùûüÿ"),
    "German": set("äöüß"),
    "Italian": set("àèéìíîòóù"),
    "Portuguese": set("ãõçáâàéêíóôú"),
}

PRACTICE_REQUESTS: Dict[str, str] = {
    "English": "Please speak and practice in English.",
    "Spanish": "Por favor, habla y practica en español.",
    "French": "Parle et entraîne-toi en français, s’il te plaît.",
    "German": "Bitte sprich und übe auf Deutsch.",
    "Italian": "Per favore, parla e fai pratica in italiano.",
    "Portuguese": "Por favor, fale e pratique em português.",
    "Chinese": "请用中文说话和练习。",
    "Japanese": "日本語で話して練習してください。",
    "Korean": "한국어로 말하고 연습해 주세요.",
    "Arabic": "يرجى التحدث والتدرّب باللغة العربية.",
}

# Han-only text can be Chinese or Japanese. These signals are used only when
# Japanese is the target, so ordinary Japanese kanji such as 学校 are not
# incorrectly rejected. Multiple signals or a distinct phrase are required.
_CHINESE_SIGNAL_PHRASES = ("你好", "谢谢", "再见", "什么", "为什么", "可以", "不是")
_CHINESE_SIGNAL_CHARACTERS = set("的了是在我你他她们这那不有吗呢很也和就都要会")


def _script_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for character in text:
        codepoint = ord(character)
        if 0x3040 <= codepoint <= 0x309F:
            counts["hiragana"] += 1
        elif 0x30A0 <= codepoint <= 0x30FF or 0xFF66 <= codepoint <= 0xFF9D:
            counts["katakana"] += 1
        elif 0xAC00 <= codepoint <= 0xD7AF or 0x1100 <= codepoint <= 0x11FF:
            counts["hangul"] += 1
        elif (
            0x0600 <= codepoint <= 0x06FF
            or 0x0750 <= codepoint <= 0x077F
            or 0x08A0 <= codepoint <= 0x08FF
            or 0xFB50 <= codepoint <= 0xFDFF
            or 0xFE70 <= codepoint <= 0xFEFF
        ):
            counts["arabic"] += 1
        elif (
            0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xF900 <= codepoint <= 0xFAFF
        ):
            counts["han"] += 1
        elif character.isalpha():
            try:
                name = unicodedata.name(character)
            except ValueError:
                name = ""
            if name.startswith("LATIN"):
                counts["latin"] += 1
            else:
                counts["other"] += 1
    return counts


def contains_han_characters(text: str) -> bool:
    """Return whether text contains a CJK unified ideograph."""

    return _script_counts(text)["han"] > 0


def has_clear_chinese_signal(text: str) -> bool:
    """Return whether Han-only text has enough evidence to be Chinese."""

    if any(phrase in text for phrase in _CHINESE_SIGNAL_PHRASES):
        return True
    signal_count = sum(character in _CHINESE_SIGNAL_CHARACTERS for character in text)
    return signal_count >= 2


def _latin_tokens(text: str) -> list[str]:
    normalized = text.casefold().replace("’", "'")
    tokens = re.findall(
        r"[^\W\d_]+(?:'[^\W\d_]+)?",
        normalized,
        flags=re.UNICODE,
    )
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        if "'" in token:
            expanded.extend(part for part in token.split("'") if part)
    return expanded


def _normalize_for_ngrams(text: str) -> str:
    normalized = text.casefold().replace("’", "'")
    normalized = "".join(
        character if character.isalpha() or character in {" ", "'"} else " "
        for character in normalized
    )
    return re.sub(r"\s+", " ", normalized).strip()


def _ngram_profile(text: str, size: int = 3) -> Counter[str]:
    normalized = f" {_normalize_for_ngrams(text)} "
    if len(normalized) < size:
        return Counter()
    return Counter(
        normalized[index : index + size]
        for index in range(len(normalized) - size + 1)
    )


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot_product = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot_product / (left_norm * right_norm)


_TOKEN_DOCUMENT_FREQUENCY: Counter[str] = Counter()
for marker_set in _LANGUAGE_WORD_MARKERS.values():
    for marker in marker_set:
        _TOKEN_DOCUMENT_FREQUENCY[marker] += 1

_CHARACTER_DOCUMENT_FREQUENCY: Counter[str] = Counter()
for character_set in _LANGUAGE_CHARACTER_HINTS.values():
    for character in character_set:
        _CHARACTER_DOCUMENT_FREQUENCY[character] += 1

_LANGUAGE_NGRAM_PROFILES = {
    language: _ngram_profile(sample)
    for language, sample in _LANGUAGE_PROFILE_TEXT.items()
}


def _detect_latin_language(text: str) -> Tuple[Optional[str], float]:
    tokens = _latin_tokens(text)
    if not tokens:
        return None, 0.0

    scores = {language: 0.0 for language in LATIN_LANGUAGES}
    evidence = {language: 0 for language in LATIN_LANGUAGES}

    for token in tokens:
        matching_languages = [
            language
            for language in LATIN_LANGUAGES
            if token in _LANGUAGE_WORD_MARKERS[language]
        ]
        for language in matching_languages:
            document_frequency = _TOKEN_DOCUMENT_FREQUENCY[token]
            weight = math.log(
                (len(LATIN_LANGUAGES) + 1) / (document_frequency + 0.5)
            ) + 0.4
            scores[language] += 2.2 * weight
            evidence[language] += 1

    for character in text.casefold():
        for language in LATIN_LANGUAGES:
            if character in _LANGUAGE_CHARACTER_HINTS[language]:
                document_frequency = _CHARACTER_DOCUMENT_FREQUENCY[character]
                weight = math.log(
                    (len(LATIN_LANGUAGES) + 1) / (document_frequency + 0.5)
                ) + 0.3
                scores[language] += 1.4 * weight

    latin_letter_count = sum(
        count
        for script, count in _script_counts(text).items()
        if script == "latin"
    )
    if latin_letter_count >= 7:
        input_profile = _ngram_profile(text)
        for language in LATIN_LANGUAGES:
            scores[language] += 2.5 * _cosine_similarity(
                input_profile,
                _LANGUAGE_NGRAM_PROFILES[language],
            )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_language, best_score = ranked[0]
    second_score = ranked[1][1]
    margin = best_score - second_score

    if best_score <= 0:
        return None, 0.0

    # A single short token is accepted only when it is a distinctive marker.
    if len(tokens) == 1:
        token = tokens[0]
        matching_languages = [
            language
            for language in LATIN_LANGUAGES
            if token in _LANGUAGE_WORD_MARKERS[language]
        ]
        if len(matching_languages) == 1 and len(token) >= 2:
            return matching_languages[0], 0.98
        return None, 0.0

    best_evidence = evidence[best_language]
    if best_evidence >= 2 and margin >= 1.2:
        confidence = min(0.99, 0.78 + margin / max(best_score, 1.0) * 0.2)
        return best_language, confidence

    if best_evidence >= 1 and len(tokens) >= 4 and margin >= 1.5:
        confidence = min(0.96, 0.74 + margin / max(best_score, 1.0) * 0.18)
        return best_language, confidence

    # Longer text can be recognized from its character patterns even when it
    # contains few beginner marker words. A generous margin avoids over-blocking.
    if latin_letter_count >= 18 and best_score >= 1.2 and margin >= 0.45:
        confidence = min(0.9, 0.68 + margin / max(best_score, 1.0) * 0.18)
        return best_language, confidence

    return None, 0.0


def detect_input_language(text: str) -> Tuple[Optional[str], float]:
    """Detect one of Lingglot's supported languages when evidence is clear.

    Returns ``(None, 0.0)`` for empty, numeric, ambiguous, or low-confidence
    input. This conservative behavior prevents the tutor from rejecting names,
    borrowed words, and other short multilingual expressions.
    """

    stripped = text.strip()
    if not stripped:
        return None, 0.0

    counts = _script_counts(stripped)
    if counts["hiragana"] or counts["katakana"]:
        return "Japanese", 0.99
    if counts["hangul"]:
        return "Korean", 0.99
    if counts["arabic"]:
        return "Arabic", 0.99
    if counts["han"]:
        return "Chinese", 0.97
    if counts["latin"]:
        return _detect_latin_language(stripped)
    return None, 0.0


def should_reject_for_target(
    text: str,
    target_language: str,
) -> Tuple[bool, Optional[str], float]:
    """Decide whether clear input-language evidence conflicts with the target."""

    detected_language, confidence = detect_input_language(text)
    if detected_language is None or detected_language == target_language:
        return False, detected_language, confidence

    # Han-only Japanese writing is inherently ambiguous. Allow ordinary kanji
    # when Japanese is selected, but reject text with strong Chinese signals.
    if (
        target_language == "Japanese"
        and detected_language == "Chinese"
        and not has_clear_chinese_signal(text)
    ):
        return False, detected_language, confidence

    return confidence >= 0.70, detected_language, confidence
