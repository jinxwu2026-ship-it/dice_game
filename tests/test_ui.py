"""Tests for practice-mode input validation and state flow."""

import unittest
from unittest.mock import patch

from the_kings_gambit.battle import run_practice
from the_kings_gambit.models import TurnState
from the_kings_gambit.ui import parse_positions, render_gamebar, show_gamebar


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


class GamebarTests(unittest.TestCase):

    def test_frame_shows_state_selected_dice_and_does_not_mutate_state(self):
        state = TurnState(match_score=400)
        before = vars(state).copy()
        frame = render_gamebar(state, 2, [1, 5, 2, 3, 4, 6], [1, 2],
                               "Ready", "Select positions, or Q")
        self.assertIn("Turn: 2", frame)
        self.assertIn("Phase: ready", frame)
        self.assertIn("Banked score: 400 / 2000", frame)
        self.assertIn("Unbanked score (at risk): 0", frame)
        self.assertIn("Dice available next: 6", frame)
        self.assertIn("[1]  [5]  [2]", frame)
        marker_line = next(line for line in frame.splitlines() if "Selected:" in line)
        self.assertEqual(marker_line.count("^"), 2)
        dice_line = next(line for line in frame.splitlines() if "Dice:" in line)
        self.assertEqual(marker_line.index("^"), dice_line.index("1"))
        self.assertEqual(vars(state), before)

    def test_long_messages_wrap_inside_ascii_border(self):
        frame = render_gamebar(TurnState(), 1, [], [],
                               "Invalid selection. " * 20, "Select positions, or Q")
        lines = frame.splitlines()
        self.assertTrue(all(len(line) == len(lines[0]) for line in lines))
        self.assertIn("waiting for the first roll", frame)

    def test_scoring_rules_are_above_gamebar_in_separate_equal_width_boxes(self):
        frame = render_gamebar(TurnState(), 1, [1, 2, 3, 4, 5, 6], [],
                               "Ready", "Select positions, or Q")
        lines = frame.splitlines()
        borders = [index for index, line in enumerate(lines) if line.startswith("+")]
        self.assertEqual(len(borders), 4)
        self.assertEqual(borders[2], borders[1] + 1)
        self.assertTrue(all(lines[index] == lines[0] for index in borders))
        self.assertTrue(all(len(line) == 66 for line in lines))
        rules = "\n".join(lines[:borders[2]])
        gamebar = "\n".join(lines[borders[2]:])
        self.assertIn("SCORING RULES", rules)
        self.assertIn("Straights: 500/600/1200", rules)
        self.assertIn("Ordinary three pairs", rules)
        self.assertNotIn("Banked score", rules)
        self.assertIn("Banked score", gamebar)
        self.assertIn("Select positions, or Q", gamebar)
        self.assertNotIn("SCORING RULES", gamebar)
        self.assertNotIn("Straights:", gamebar)

    def test_captured_output_does_not_clear_terminal(self):
        outputs = []
        with patch("the_kings_gambit.ui.os.system") as clear:
            show_gamebar(TurnState(), 1, [], [], "Ready", "Select", outputs.append)
        clear.assert_not_called()
        self.assertEqual(len(outputs), 1)

    def test_interactive_output_clears_before_redrawing(self):
        with patch("the_kings_gambit.ui.sys.stdout.isatty", return_value=True), \
             patch("the_kings_gambit.ui.os.system") as clear, \
             patch("builtins.print") as output:
            show_gamebar(TurnState(), 1, [], [], "Ready", "Select", output)
        clear.assert_called_once()
        self.assertIn(clear.call_args.args[0], ("cls", "clear"))
        output.assert_called_once()


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
        pair_frames = [frame for frame in outputs if "Phase: ready" in frame]
        self.assertEqual(len(pair_frames), 2)
        self.assertTrue(all("THREE PAIRS: +0" in frame for frame in pair_frames))
        self.assertTrue(all("Immediate six-die reroll" in frame for frame in pair_frames))
        self.assertTrue(all("[B]ank" not in frame for frame in pair_frames))

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

    def test_gamebar_tracks_bank_new_turn_and_bust(self):
        outputs = []
        score = run_practice(
            make_input(["1", "b", "", "1", "r", "q"]), outputs.append,
            FakeRandom([1, 2, 3, 4, 6, 6] * 2 + [2, 3, 3, 4, 6]))
        self.assertEqual(score, 100)
        bank = next(frame for frame in outputs if "Banked!" in frame)
        self.assertIn("Phase: ended", bank)
        self.assertIn("Banked score: 100 / 2000", bank)
        self.assertIn("Unbanked score (at risk): 0", bank)
        second_turn = next(frame for frame in outputs
                           if "Turn: 2" in frame and "Phase: select" in frame)
        self.assertIn("Dice available next: 6", second_turn)
        bust = next(frame for frame in outputs if "BUST!" in frame)
        self.assertIn("Banked score: 100 / 2000", bust)
        self.assertIn("Unbanked score (at risk): 0", bust)
        self.assertIn("Dice available next: 0", bust)
        self.assertIn("Phase: ended", bust)
        self.assertNotIn("[B]ank", bust)

    def test_invalid_next_turn_command_does_not_start_a_turn(self):
        outputs = []
        score = run_practice(make_input(["1", "b", "wrong", "q"]),
                             outputs.append, FakeRandom([1, 2, 3, 4, 6, 6]))
        self.assertEqual(score, 100)
        self.assertTrue(any("Invalid command" in frame for frame in outputs))
        self.assertFalse(any("Turn: 2" in frame for frame in outputs))

    def test_interrupt_at_each_prompt_exits_with_only_banked_score(self):
        for error in (EOFError, KeyboardInterrupt):
            for answers, expected in [([], 0), (["1"], 0), (["1", "b"], 100)]:
                with self.subTest(error=error, answers=answers):
                    inputs = iter(answers)

                    def answer(prompt):
                        try:
                            return next(inputs)
                        except StopIteration:
                            raise error()

                    outputs = []
                    score = run_practice(answer, outputs.append,
                                         FakeRandom([1, 2, 3, 4, 6, 6]))
                    self.assertEqual(score, expected)
                    self.assertIn("Practice ended", outputs[-1])


if __name__ == "__main__":
    unittest.main()
