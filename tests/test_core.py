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
    generate_vocab_question,
    language_learning_turn,
    learner_history_dataframe,
    predict_learner_profile,
    validate_target_language_input,
)


class CoreLogicTests(unittest.TestCase):
    def test_chinese_character_detection(self) -> None:
        self.assertTrue(contains_chinese_characters("\u4f60\u597d"))
        self.assertFalse(contains_chinese_characters("Hello there"))

    def test_english_language_guard(self) -> None:
        result = validate_target_language_input("\u4f60\u597d", "English")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["points"], 0)
        self.assertIn("English", result["ai_reply"])

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
