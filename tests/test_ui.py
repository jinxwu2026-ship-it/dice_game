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
        self.assertEqual(final_score, 1500)
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


if __name__ == "__main__":
    unittest.main()
