"""Core learning logic for the Lingglot Streamlit application.

This module contains the algorithms from the original Streamlit prototype and
has no dependency on Streamlit itself. Keeping the learning logic separate
makes it easier to test, reuse, and later expose through an API.
"""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .language_detection import (
    PRACTICE_REQUESTS,
    contains_han_characters,
    detect_input_language,
    should_reject_for_target,
)

APP_NAME = "Lingglot - AI Language Learning"
AUTHOR = "Isabella Fu"
MENTOR = "Qingyang Xiao"
ADVISOR = MENTOR
MODEL_NAME = "google/flan-t5-small"

SUPPORTED_LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Chinese",
    "Japanese",
    "Korean",
    "Arabic",
]

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

CHARACTER_PERSONA = """
You are Luna, a friendly AI language-learning character.
You help the learner practice a target foreign language.
You must respond in the selected target language.
You should be warm, simple, encouraging, and educational.
Ask one short follow-up question to continue the conversation.
"""

# The original vocabulary banks are retained and expanded so all selectable
# languages have target-language content.
VOCAB_BANK: Dict[str, List[Tuple[str, str]]] = {
    "Spanish": [
        ("hello", "hola"),
        ("thank you", "gracias"),
        ("water", "agua"),
        ("friend", "amigo"),
        ("school", "escuela"),
    ],
    "French": [
        ("hello", "bonjour"),
        ("thank you", "merci"),
        ("water", "eau"),
        ("friend", "ami"),
        ("school", "ecole"),
    ],
    "German": [
        ("hello", "hallo"),
        ("thank you", "danke"),
        ("water", "wasser"),
        ("friend", "freund"),
        ("school", "schule"),
    ],
    "Italian": [
        ("hello", "ciao"),
        ("thank you", "grazie"),
        ("water", "acqua"),
        ("friend", "amico"),
        ("school", "scuola"),
    ],
    "Portuguese": [
        ("hello", "ola"),
        ("thank you", "obrigado"),
        ("water", "agua"),
        ("friend", "amigo"),
        ("school", "escola"),
    ],
    "Chinese": [
        ("hello", "\u4f60\u597d"),
        ("thank you", "\u8c22\u8c22"),
        ("water", "\u6c34"),
        ("friend", "\u670b\u53cb"),
        ("school", "\u5b66\u6821"),
    ],
    "Japanese": [
        ("hello", "\u3053\u3093\u306b\u3061\u306f"),
        ("thank you", "\u3042\u308a\u304c\u3068\u3046"),
        ("water", "\u6c34"),
        ("friend", "\u53cb\u9054"),
        ("school", "\u5b66\u6821"),
    ],
    "Korean": [
        ("hello", "\uc548\ub155\ud558\uc138\uc694"),
        ("thank you", "\uac10\uc0ac\ud569\ub2c8\ub2e4"),
        ("water", "\ubb3c"),
        ("friend", "\uce5c\uad6c"),
        ("school", "\ud559\uad50"),
    ],
    "Arabic": [
        ("hello", "\u0645\u0631\u062d\u0628\u0627"),
        ("thank you", "\u0634\u0643\u0631\u0627"),
        ("water", "\u0645\u0627\u0621"),
        ("friend", "\u0635\u062f\u064a\u0642"),
        ("school", "\u0645\u062f\u0631\u0633\u0629"),
    ],
    "English": [
        ("hola", "hello"),
        ("gracias", "thank you"),
        ("agua", "water"),
        ("amigo", "friend"),
        ("escuela", "school"),
    ],
}

ROLEPLAY_SCENARIOS = [
    "ordering food at a small restaurant",
    "introducing yourself to a new classmate",
    "asking for directions in a city",
    "talking about your favorite hobby",
    "checking in at a hotel",
    "buying a train ticket",
]

FEATURE_COLUMNS = [
    "turns",
    "avg_words",
    "mistakes_per_turn",
    "points_per_turn",
    "mini_game_wins",
]


@dataclass
class LearnerState:
    """Keep one learner's progress for the current application session."""

    username: str = "Guest Learner"
    target_language: str = "Spanish"
    difficulty: str = "Beginner"
    total_points: int = 0
    conversation_turns: int = 0
    total_words: int = 0
    estimated_mistakes: int = 0
    mini_game_wins: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)


class DifficultyBandit:
    """Simple epsilon-greedy bandit for adaptive difficulty selection."""

    def __init__(
        self,
        difficulties: Optional[List[str]] = None,
        epsilon: float = 0.15,
    ) -> None:
        self.difficulties = difficulties or DIFFICULTY_LEVELS.copy()
        self.epsilon = epsilon
        self.counts = {difficulty: 0 for difficulty in self.difficulties}
        self.values = {difficulty: 10.0 for difficulty in self.difficulties}

    def choose_difficulty(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.difficulties)
        return max(self.values, key=self.values.get)

    def update(self, difficulty: str, reward: float) -> None:
        self.counts[difficulty] += 1
        count = self.counts[difficulty]
        self.values[difficulty] += (reward - self.values[difficulty]) / count

    def summary(self) -> Dict[str, Dict[str, float | int]]:
        return {
            "counts": self.counts.copy(),
            "estimated_values": {
                key: round(value, 2) for key, value in self.values.items()
            },
        }


def build_chat_prompt(
    user_message: str,
    target_language: str,
    difficulty: str,
) -> str:
    return f"""
{CHARACTER_PERSONA}
Target language: {target_language}
Learner difficulty level: {difficulty}
Learner message: {user_message}
Task: Reply naturally in {target_language}, match {difficulty} level, keep it concise, and ask one follow-up question.
"""


def build_feedback_prompt(
    user_message: str,
    target_language: str,
    difficulty: str,
) -> str:
    return f"""
You are a language tutor.
Target language: {target_language}
Learner difficulty: {difficulty}
Learner sentence: {user_message}
Give brief feedback in English: corrected version if needed, grammar issue, better phrase, and encouragement.
"""


def fallback_character_reply(
    user_message: str,
    target_language: str,
    difficulty: str,
) -> str:
    del user_message, difficulty
    templates = {
        "English": "Great! I understand. Can you tell me a little more about that?",
        "Spanish": "\u00a1Muy bien! Entiendo. \u00bfPuedes contarme un poco m\u00e1s sobre eso?",
        "French": "Tr\u00e8s bien ! Je comprends. Peux-tu m'en dire un peu plus ?",
        "German": "Sehr gut! Ich verstehe. Kannst du mir ein bisschen mehr dar\u00fcber erz\u00e4hlen?",
        "Italian": "Molto bene! Capisco. Puoi dirmi qualcosa di pi\u00f9?",
        "Portuguese": "Muito bem! Eu entendo. Voc\u00ea pode me contar um pouco mais?",
        "Chinese": "\u5f88\u597d\uff01\u6211\u660e\u767d\u4f60\u7684\u610f\u601d\u3002\u4f60\u53ef\u4ee5\u518d\u591a\u8bf4\u4e00\u70b9\u5417\uff1f",
        "Japanese": "\u3044\u3044\u3067\u3059\u306d\uff01\u308f\u304b\u308a\u307e\u3057\u305f\u3002\u3082\u3046\u5c11\u3057\u8a73\u3057\u304f\u6559\u3048\u3066\u304f\u308c\u307e\u3059\u304b\uff1f",
        "Korean": "\uc88b\uc544\uc694! \uc774\ud574\ud588\uc5b4\uc694. \uc870\uae08 \ub354 \ub9d0\ud574 \uc904 \uc218 \uc788\ub098\uc694?",
        "Arabic": "\u062c\u064a\u062f \u062c\u062f\u064b\u0627! \u0623\u0641\u0647\u0645. \u0647\u0644 \u064a\u0645\u0643\u0646\u0643 \u0623\u0646 \u062a\u062e\u0628\u0631\u0646\u064a \u0628\u0627\u0644\u0645\u0632\u064a\u062f\u061f",
    }
    return templates.get(target_language, templates["English"])


def fallback_feedback(
    user_message: str,
    target_language: str,
    difficulty: str,
) -> str:
    del target_language, difficulty
    if len(user_message.split()) < 3:
        return (
            "Good start. Try to write a fuller sentence with a subject, "
            "verb, and one extra detail."
        )
    if user_message and user_message[0].islower():
        return (
            "Nice practice. One small improvement: begin the sentence with "
            "a capital letter when the language uses capitalization."
        )
    return (
        "Nice sentence. For better fluency, add one connector word, one "
        "descriptive phrase, or one follow-up question."
    )


@lru_cache(maxsize=2)
def load_huggingface_generator(model_name: str):
    """Load the optional local Hugging Face text-to-text generator."""

    try:
        from transformers import pipeline

        generator = pipeline(
            "text2text-generation",
            model=model_name,
            max_new_tokens=160,
        )
        return generator, None
    except Exception as exc:  # pragma: no cover - optional UI path
        return None, str(exc)


def generate_with_llm(
    prompt: str,
    fallback: str,
    use_llm: bool = False,
) -> Tuple[str, Optional[str]]:
    if not use_llm:
        return fallback, None

    generator, error = load_huggingface_generator(MODEL_NAME)
    if generator is None:
        return fallback, error

    try:
        output = generator(prompt)
        text = output[0].get("generated_text", "").strip()
        return text if text else fallback, None
    except Exception as exc:  # pragma: no cover - optional UI path
        return fallback, str(exc)


def contains_chinese_characters(text: str) -> bool:
    """Return True when learner input contains Chinese CJK characters."""

    return contains_han_characters(text)


def validate_target_language_input(
    user_message: str,
    target_language: str,
) -> Optional[Dict[str, Any]]:
    """Return tutor guidance when the message clearly uses another language.

    Detection is conservative: ambiguous single words and names are accepted,
    while clear mismatches across all supported languages receive a localized
    request to continue in the currently selected practice language.
    """

    should_reject, detected_language, confidence = should_reject_for_target(
        user_message,
        target_language,
    )
    if not should_reject:
        return None

    detected_description = detected_language or "another language"
    return {
        "ai_reply": PRACTICE_REQUESTS.get(
            target_language,
            f"Please speak and practice in {target_language}.",
        ),
        "feedback": (
            f"Your target practice language is {target_language}, but your "
            f"message appears to be {detected_description}. Try rewriting your "
            f"message in {target_language} so Luna can help you improve."
        ),
        "points": 0,
        "llm_error": None,
        "detected_language": detected_language,
        "detection_confidence": confidence,
    }


def estimate_mistakes_simple(text: str) -> int:
    mistakes = 0
    if len(text.strip()) == 0:
        mistakes += 1
    if len(text.split()) < 3:
        mistakes += 1
    if text and text[0].islower():
        mistakes += 1
    mistakes += len(re.findall(r"\s{2,}", text))
    return mistakes


def calculate_reward(
    user_message: str,
    feedback: str,
    difficulty: str,
) -> int:
    del feedback
    points = 10
    words = len(user_message.split())
    mistakes = estimate_mistakes_simple(user_message)
    if words >= 8:
        points += 5
    if mistakes == 0:
        points += 5
    if difficulty == "Intermediate":
        points += 3
    if difficulty == "Advanced":
        points += 6
    return max(points - 2 * mistakes, 1)


def update_learner_state(
    state: LearnerState,
    user_message: str,
    ai_reply: str,
    feedback: str,
    points: int,
) -> LearnerState:
    mistakes = estimate_mistakes_simple(user_message)
    words = len(user_message.split())
    state.total_points += points
    state.conversation_turns += 1
    state.total_words += words
    state.estimated_mistakes += mistakes
    state.history.append(
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_language": state.target_language,
            "difficulty": state.difficulty,
            "user_message": user_message,
            "ai_reply": ai_reply,
            "feedback": feedback,
            "points": points,
            "words": words,
            "estimated_mistakes": mistakes,
        }
    )
    return state


def generate_synthetic_training_profiles(
    n: int = 120,
    random_seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    rows: List[Dict[str, Any]] = []
    for _ in range(n):
        profile_type = rng.choice(
            ["beginner", "steady", "advanced", "needs_support"]
        )
        if profile_type == "beginner":
            turns, avg_words, mistakes, points, wins = (
                rng.integers(1, 15),
                rng.normal(4, 1),
                rng.normal(1.8, 0.5),
                rng.normal(8, 2),
                rng.integers(0, 3),
            )
        elif profile_type == "steady":
            turns, avg_words, mistakes, points, wins = (
                rng.integers(10, 60),
                rng.normal(9, 2),
                rng.normal(0.8, 0.3),
                rng.normal(14, 3),
                rng.integers(1, 8),
            )
        elif profile_type == "advanced":
            turns, avg_words, mistakes, points, wins = (
                rng.integers(30, 120),
                rng.normal(18, 4),
                rng.normal(0.4, 0.2),
                rng.normal(20, 4),
                rng.integers(5, 20),
            )
        else:
            turns, avg_words, mistakes, points, wins = (
                rng.integers(5, 40),
                rng.normal(7, 2),
                rng.normal(2.5, 0.6),
                rng.normal(7, 2),
                rng.integers(0, 5),
            )
        rows.append(
            {
                "turns": max(float(turns), 1.0),
                "avg_words": max(float(avg_words), 1.0),
                "mistakes_per_turn": max(float(mistakes), 0.0),
                "points_per_turn": max(float(points), 1.0),
                "mini_game_wins": max(float(wins), 0.0),
                "true_profile": profile_type,
            }
        )
    return pd.DataFrame(rows)


def interpret_cluster(cluster_id: int, summary_df: pd.DataFrame) -> str:
    row = summary_df.loc[cluster_id]
    if row["avg_words"] >= 14 and row["mistakes_per_turn"] < 1:
        return "Advanced conversational learner"
    if row["mistakes_per_turn"] >= 1.8:
        return "Learner needing grammar and sentence-structure support"
    if row["turns"] < 20:
        return "Early-stage beginner learner"
    return "Consistent conversational learner"


@lru_cache(maxsize=1)
def build_profile_model():
    profile_df = generate_synthetic_training_profiles()
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(profile_df[FEATURE_COLUMNS])
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    profile_df["cluster"] = kmeans.fit_predict(scaled_features)
    cluster_summary = (
        profile_df.groupby("cluster")[FEATURE_COLUMNS].mean().round(2)
    )
    cluster_labels = {
        cluster_id: interpret_cluster(cluster_id, cluster_summary)
        for cluster_id in cluster_summary.index
    }
    return scaler, kmeans, cluster_summary, cluster_labels


def learner_features_from_state(state: LearnerState) -> pd.DataFrame:
    turns = max(state.conversation_turns, 1)
    feature_row = {
        "turns": state.conversation_turns,
        "avg_words": state.total_words / turns,
        "mistakes_per_turn": state.estimated_mistakes / turns,
        "points_per_turn": state.total_points / turns,
        "mini_game_wins": state.mini_game_wins,
    }
    return pd.DataFrame([feature_row], columns=FEATURE_COLUMNS)


def predict_learner_profile(state: LearnerState) -> str:
    scaler, kmeans, _cluster_summary, cluster_labels = build_profile_model()
    features = learner_features_from_state(state)
    cluster = int(kmeans.predict(scaler.transform(features))[0])
    return cluster_labels.get(cluster, "General learner profile")


def language_learning_turn(
    state: LearnerState,
    bandit: DifficultyBandit,
    user_message: str,
    target_language: str,
    selected_difficulty: str,
    auto_adapt_difficulty: bool = True,
    use_llm: bool = False,
) -> Tuple[Dict[str, Any], LearnerState, DifficultyBandit]:
    if not user_message or not user_message.strip():
        result = {
            "ai_reply": "Please enter a message first.",
            "feedback": "No input detected.",
            "points": 0,
            "total_points": state.total_points,
            "profile": predict_learner_profile(state),
            "difficulty": state.difficulty,
            "bandit": bandit.summary(),
            "llm_error": None,
        }
        return result, state, bandit

    state.target_language = target_language
    difficulty = (
        bandit.choose_difficulty()
        if auto_adapt_difficulty
        else selected_difficulty
    )
    state.difficulty = difficulty

    validation_result = validate_target_language_input(
        user_message.strip(),
        target_language,
    )
    if validation_result:
        learner_profile = predict_learner_profile(state)
        state.history.append(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "target_language": state.target_language,
                "difficulty": state.difficulty,
                "user_message": user_message,
                "ai_reply": validation_result["ai_reply"],
                "feedback": validation_result["feedback"],
                "points": validation_result["points"],
                "words": len(user_message.split()),
                "estimated_mistakes": 0,
            }
        )
        result = {
            "ai_reply": validation_result["ai_reply"],
            "feedback": validation_result["feedback"],
            "points": validation_result["points"],
            "total_points": state.total_points,
            "profile": learner_profile,
            "difficulty": difficulty,
            "bandit": bandit.summary(),
            "llm_error": validation_result["llm_error"],
        }
        return result, state, bandit

    ai_reply, chat_error = generate_with_llm(
        build_chat_prompt(user_message, target_language, difficulty),
        fallback_character_reply(user_message, target_language, difficulty),
        use_llm=use_llm,
    )
    feedback, feedback_error = generate_with_llm(
        build_feedback_prompt(user_message, target_language, difficulty),
        fallback_feedback(user_message, target_language, difficulty),
        use_llm=use_llm,
    )

    points = calculate_reward(user_message, feedback, difficulty)
    state = update_learner_state(
        state,
        user_message,
        ai_reply,
        feedback,
        points,
    )
    learner_profile = predict_learner_profile(state)
    bandit.update(
        difficulty,
        points - 2 * estimate_mistakes_simple(user_message),
    )

    result = {
        "ai_reply": ai_reply,
        "feedback": feedback,
        "points": points,
        "total_points": state.total_points,
        "profile": learner_profile,
        "difficulty": difficulty,
        "bandit": bandit.summary(),
        "llm_error": chat_error or feedback_error,
    }
    return result, state, bandit


def generate_vocab_question(target_language: str) -> Tuple[str, str]:
    bank = VOCAB_BANK.get(target_language, VOCAB_BANK["Spanish"])
    source, target = random.choice(bank)
    return f"Translate '{source}' into {target_language}.", target


def check_vocab_answer(answer: str, correct_answer: str) -> Tuple[bool, str]:
    is_correct = answer.strip().casefold() == correct_answer.strip().casefold()
    if is_correct:
        return True, "Correct! +15 points."
    return False, f"Good try. The expected answer is: {correct_answer}"


def generate_roleplay_prompt(target_language: str, difficulty: str) -> str:
    scenario = random.choice(ROLEPLAY_SCENARIOS)
    return (
        f"Role-play in {target_language}: You are {scenario}. "
        f"Write one sentence at {difficulty} level to continue."
    )


def sentence_expansion_challenge(target_language: str) -> str:
    return (
        f"Sentence challenge in {target_language}: Write a longer sentence "
        "using one emotion word, one time word, and one reason."
    )


def learner_history_dataframe(state: LearnerState) -> pd.DataFrame:
    if not state.history:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "target_language",
                "difficulty",
                "user_message",
                "ai_reply",
                "feedback",
                "points",
                "words",
                "estimated_mistakes",
            ]
        )
    return pd.DataFrame(state.history)


def calculate_skill_scores(state: LearnerState) -> Dict[str, int]:
    """Derive friendly visual progress indicators from session statistics."""

    turns = max(state.conversation_turns, 1)
    avg_words = state.total_words / turns
    mistakes_per_turn = state.estimated_mistakes / turns
    points_per_turn = state.total_points / turns

    fluency = min(100, int(25 + avg_words * 4.2 + state.conversation_turns * 1.2))
    accuracy = max(0, min(100, int(100 - mistakes_per_turn * 24)))
    vocabulary = min(100, int(25 + state.mini_game_wins * 10 + avg_words * 2.2))
    consistency = min(100, int(15 + state.conversation_turns * 6))
    confidence = min(100, int(20 + points_per_turn * 3.2))

    return {
        "Fluency": fluency,
        "Accuracy": accuracy,
        "Vocabulary": vocabulary,
        "Consistency": consistency,
        "Confidence": confidence,
    }
