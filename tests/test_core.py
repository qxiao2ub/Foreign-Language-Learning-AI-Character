from __future__ import annotations

import unittest

from lingglot.core import (
    DIFFICULTY_LEVELS,
    SUPPORTED_LANGUAGES,
    DifficultyBandit,
    LearnerState,
    calculate_reward,
    check_vocab_answer,
    contains_chinese_characters,
    detect_input_language,
    generate_vocab_question,
    language_learning_turn,
    learner_history_dataframe,
    predict_learner_profile,
    validate_target_language_input,
)


class CoreLogicTests(unittest.TestCase):
    def test_chinese_character_detection(self) -> None:
        self.assertTrue(contains_chinese_characters("你好"))
        self.assertFalse(contains_chinese_characters("Hello there"))

    def test_english_language_guard(self) -> None:
        result = validate_target_language_input("你好", "English")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["points"], 0)
        self.assertIn("English", result["ai_reply"])
        self.assertEqual(result["detected_language"], "Chinese")

    def test_detects_every_supported_language(self) -> None:
        samples = {
            "English": "Hello, how are you today?",
            "Spanish": "Hola, me gusta aprender español hoy.",
            "French": "Bonjour, je voudrais parler avec vous.",
            "German": "Hallo, ich möchte heute Deutsch lernen.",
            "Italian": "Ciao, mi piace imparare le lingue.",
            "Portuguese": "Olá, eu quero falar português hoje.",
            "Chinese": "你好，我今天很好。",
            "Japanese": "こんにちは。今日は元気ですか？",
            "Korean": "안녕하세요. 오늘 기분이 어때요?",
            "Arabic": "مرحبا، كيف حالك اليوم؟",
        }
        for expected_language, sample in samples.items():
            with self.subTest(language=expected_language):
                detected_language, confidence = detect_input_language(sample)
                self.assertEqual(detected_language, expected_language)
                self.assertGreaterEqual(confidence, 0.70)

    def test_wrong_language_guard_works_for_every_target(self) -> None:
        mismatches = {
            "English": "Hola, me gusta aprender español.",
            "Spanish": "Hello, I want to practice today.",
            "French": "Hallo, ich möchte Deutsch lernen.",
            "German": "Ciao, mi piace imparare le lingue.",
            "Italian": "Bonjour, je voudrais parler avec vous.",
            "Portuguese": "Good morning, how are you today?",
            "Chinese": "こんにちは。今日は元気ですか？",
            "Japanese": "안녕하세요. 오늘 기분이 어때요?",
            "Korean": "مرحبا، كيف حالك اليوم؟",
            "Arabic": "你好，我今天很好。",
        }
        for target_language, sample in mismatches.items():
            with self.subTest(target=target_language):
                result = validate_target_language_input(sample, target_language)
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result["points"], 0)
                self.assertIn(target_language, result["feedback"])
                self.assertTrue(result["ai_reply"])

    def test_matching_language_is_allowed_for_every_target(self) -> None:
        samples = {
            "English": "Hello, I want to practice English today.",
            "Spanish": "Hola, quiero practicar español hoy.",
            "French": "Bonjour, je veux pratiquer le français aujourd'hui.",
            "German": "Hallo, ich möchte heute Deutsch üben.",
            "Italian": "Ciao, oggi voglio praticare l'italiano.",
            "Portuguese": "Olá, hoje quero praticar português.",
            "Chinese": "你好，我想练习中文。",
            "Japanese": "こんにちは。日本語を練習したいです。",
            "Korean": "안녕하세요. 한국어를 연습하고 싶어요.",
            "Arabic": "مرحبا، أريد أن أتدرب على العربية.",
        }
        for target_language, sample in samples.items():
            with self.subTest(target=target_language):
                self.assertIsNone(
                    validate_target_language_input(sample, target_language)
                )

    def test_ambiguous_short_input_is_not_blocked(self) -> None:
        for target_language in SUPPORTED_LANGUAGES:
            with self.subTest(target=target_language):
                self.assertIsNone(
                    validate_target_language_input("pizza", target_language)
                )

    def test_shared_spanish_portuguese_word_is_not_overblocked(self) -> None:
        self.assertIsNone(validate_target_language_input("agua", "Spanish"))
        self.assertIsNone(validate_target_language_input("agua", "Portuguese"))

    def test_japanese_kanji_only_input_is_not_mistaken_for_chinese(self) -> None:
        self.assertIsNone(validate_target_language_input("日本語学校", "Japanese"))
        self.assertIsNotNone(validate_target_language_input("你好", "Japanese"))

    def test_guard_turn_does_not_award_points(self) -> None:
        state = LearnerState(target_language="Spanish")
        bandit = DifficultyBandit(epsilon=0.0)
        result, state, _bandit = language_learning_turn(
            state,
            bandit,
            "Hello, how are you today?",
            "Spanish",
            "Beginner",
            auto_adapt_difficulty=False,
            use_llm=False,
        )
        self.assertEqual(result["points"], 0)
        self.assertEqual(state.total_points, 0)
        self.assertIn("español", result["ai_reply"])

    def test_reward_is_positive(self) -> None:
        points = calculate_reward(
            "I enjoy learning languages with my friends today.",
            "Nice sentence.",
            "Intermediate",
        )
        self.assertGreater(points, 0)

    def test_fallback_turn_updates_state_and_bandit(self) -> None:
        state = LearnerState(target_language="Spanish")
        bandit = DifficultyBandit(epsilon=0.0)
        result, state, bandit = language_learning_turn(
            state,
            bandit,
            "Me gusta aprender idiomas hoy.",
            "Spanish",
            "Beginner",
            auto_adapt_difficulty=False,
            use_llm=False,
        )
        self.assertEqual(state.conversation_turns, 1)
        self.assertEqual(len(state.history), 1)
        self.assertGreater(state.total_points, 0)
        self.assertEqual(result["difficulty"], "Beginner")
        self.assertEqual(bandit.counts["Beginner"], 1)

    def test_profile_prediction_returns_label(self) -> None:
        label = predict_learner_profile(LearnerState())
        self.assertIsInstance(label, str)
        self.assertTrue(label)

    def test_every_language_has_a_vocab_question(self) -> None:
        for language in SUPPORTED_LANGUAGES:
            question, answer = generate_vocab_question(language)
            self.assertIn(language, question)
            self.assertTrue(answer)

    def test_vocab_answer_uses_casefold(self) -> None:
        correct, _message = check_vocab_answer("HELLO", "hello")
        self.assertTrue(correct)

    def test_empty_history_dataframe_has_expected_columns(self) -> None:
        frame = learner_history_dataframe(LearnerState())
        self.assertIn("timestamp", frame.columns)
        self.assertIn("points", frame.columns)
        self.assertTrue(frame.empty)

    def test_bandit_has_all_difficulties(self) -> None:
        bandit = DifficultyBandit()
        self.assertEqual(set(bandit.counts), set(DIFFICULTY_LEVELS))


if __name__ == "__main__":
    unittest.main()
