"""Tests for practice-mode input validation and state flow."""

import unittest

from the_kings_gambit.ui import parse_positions, run_practice


class FakeRandom:
    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        return self.values.pop(0)


def make_input(values):
    """Create a replacement for input() that returns prepared answers."""
    answers = iter(values)
    return lambda prompt: next(answers)


class ParsePositionsTests(unittest.TestCase):

    def test_accepts_spaces_and_commas(self):
        self.assertEqual(parse_positions("1, 3 5"), [1, 3, 5])

    def test_rejects_empty_and_non_number_input(self):
        for text in ("", "one", "1 two"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_positions(text)


class PracticeModeTests(unittest.TestCase):

    def test_player_can_score_bank_and_quit(self):
        outputs = []
        final_score = run_practice(
            input_func=make_input(["1 2 3 4 5 6", "b", "q"]),
            output_func=outputs.append,
            random_source=FakeRandom([1, 2, 3, 4, 5, 6]),
        )
        self.assertEqual(final_score, 1200)
        self.assertTrue(any("HOT DICE" in line for line in outputs))
        self.assertTrue(any("Banked" in line for line in outputs))

    def test_bust_loses_unbanked_points(self):
        outputs = []
        final_score = run_practice(
            input_func=make_input(["1", "r", "q"]),
            output_func=outputs.append,
            random_source=FakeRandom([1, 2, 3, 4, 6, 6, 2, 3, 3, 4, 6]),
        )
        self.assertEqual(final_score, 0)
        self.assertTrue(any("BUST" in line for line in outputs))

    def test_invalid_selection_is_explained_and_retried(self):
        outputs = []
        final_score = run_practice(
            input_func=make_input(["2", "1", "b", "q"]),
            output_func=outputs.append,
            random_source=FakeRandom([1, 2, 3, 4, 6, 6]),
        )
        self.assertEqual(final_score, 100)
        self.assertTrue(any("Invalid selection" in line for line in outputs))


    def test_ordinary_pairs_reroll_without_bank_prompt(self):
        prompts = []
        answers = iter(["1 2 3 4 5 6", "r", "1 2 3 4 5 6",
                        "1 2 3 4 5 6", "1", "b", "q"])

        def answer(prompt):
            prompts.append(prompt)
            return next(answers)

        outputs = []
        score = run_practice(answer, outputs.append, FakeRandom(
            [1, 1, 1, 5, 5, 5] + [2, 2, 4, 4, 6, 6]
            + [1, 1, 3, 3, 6, 6] + [1, 2, 3, 4, 6, 6]))
        self.assertEqual(score, 1100)
        self.assertEqual(sum("[B]ank" in prompt for prompt in prompts), 2)
        self.assertEqual(sum("THREE PAIRS: +0" in line for line in outputs), 2)

    def test_bank_at_target_exits_without_another_turn(self):
        for last_roll, expected in [([2, 2, 2, 2, 2, 2], 2000),
                                    ([1, 2, 3, 4, 5, 6], 2400)]:
            outputs = []
            score = run_practice(
                make_input(["1 2 3 4 5 6", "b", "", "1 2 3 4 5 6", "b"]),
                outputs.append, FakeRandom([1, 2, 3, 4, 5, 6] + last_roll))
            self.assertEqual(score, expected)
            self.assertTrue(any("VICTORY" in line for line in outputs))

    def test_malformed_selections_and_commands_retry_same_roll(self):
        outputs = []
        score = run_practice(
            make_input(["", "one", "1 1", "0", "7", "1", "wrong", "b", "q"]),
            outputs.append, FakeRandom([1, 2, 3, 4, 6, 6]))
        self.assertEqual(score, 100)
        self.assertEqual(sum("Invalid selection" in line for line in outputs), 5)
        self.assertTrue(any("Invalid command" in line for line in outputs))

    def test_eof_and_interrupt_exit_cleanly(self):
        for error in (EOFError, KeyboardInterrupt):
            def closed_input(prompt):
                raise error()

            score = run_practice(closed_input, lambda line: None,
                                 FakeRandom([1, 2, 3, 4, 6, 6]))
            self.assertEqual(score, 0)


if __name__ == "__main__":
    unittest.main()
