"""Deterministic checks for Easy AI choices, pacing, and one complete match."""

import unittest

from the_kings_gambit.battle import (
    ai_decision, begin_roll, choose_ai_selection, resolve_roll, run_match,
)
from the_kings_gambit.models import MatchState, TurnState


class FixedRandom:
    """Feed exact dice values; running out exposes an unexpected extra roll."""

    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    def randint(self, low, high):
        self.calls.append((low, high))
        value = next(self.values)
        if not low <= value <= high:
            raise AssertionError("test value is outside the requested range")
        return value


class EasyDecisionTests(unittest.TestCase):

    def test_highest_immediate_score_uses_valid_positions(self):
        action = choose_ai_selection([3, 3, 3, 5, 6, 6])
        self.assertEqual(action["selected_positions"], [1, 2, 3, 4])
        self.assertEqual(action["score_delta"], 350)

    def test_equal_scores_choose_lexicographically_earliest_positions(self):
        # Either of the two 4s can complete a 500-point straight.
        for _ in range(3):
            action = choose_ai_selection([1, 2, 3, 4, 4, 5])
            self.assertEqual(action["selected_positions"], [1, 2, 3, 4, 6])
            self.assertEqual(action["score_delta"], 500)

    def test_zero_pairs_are_used_only_if_no_positive_selection_exists(self):
        zero = choose_ai_selection([2, 2, 4, 4, 6, 6])
        self.assertEqual(zero["action_type"], "ordinary_pairs")
        positive = choose_ai_selection([1, 1, 3, 3, 6, 6])
        self.assertEqual(positive["selected_positions"], [1, 2])
        self.assertEqual(positive["score_delta"], 200)

    def test_consecutive_pairs_score_instead_of_zero_reroll(self):
        action = choose_ai_selection([2, 2, 3, 3, 4, 4])
        self.assertEqual(action["action_type"], "score")
        self.assertEqual(action["score_delta"], 1000)

    def test_no_legal_actions_means_bust(self):
        self.assertIsNone(choose_ai_selection([2, 3, 3, 4, 6, 6]))

    def test_below_equal_and_above_ambition(self):
        cases = [([4, 4, 4, 5, 2, 6], 450, "roll"),
                 ([1, 4, 4, 4, 2, 6], 500, "bank"),
                 ([6, 6, 6, 2, 3, 4], 600, "bank")]
        for roll, score, expected in cases:
            with self.subTest(score=score):
                state = TurnState()
                resolve_roll(state, roll, choose_ai_selection(roll)["selected_positions"])
                before = vars(state).copy()
                command, reason = ai_decision(state, 500)
                self.assertEqual(command, expected)
                self.assertIn("ambition 500", reason)
                self.assertEqual(vars(state), before)

    def test_winning_bank_has_priority_even_below_ambition(self):
        state = TurnState(match_score=1950)
        resolve_roll(state, [5, 2, 3, 4, 6, 6], [1])
        command, reason = ai_decision(state, 500)
        self.assertEqual(command, "bank")
        self.assertIn("wins immediately", reason)
        self.assertFalse(state.has_won)
        state.bank()
        self.assertTrue(state.has_won)

    def test_bank_decision_is_unavailable_before_selection_or_after_pairs(self):
        state = TurnState()
        with self.assertRaises(ValueError):
            ai_decision(state, 500)
        begin_roll(state, [2, 2, 4, 4, 6, 6])
        with self.assertRaises(ValueError):
            ai_decision(state, 500)
        resolve_roll(state, [2, 2, 4, 4, 6, 6], [1, 2, 3, 4, 5, 6])
        with self.assertRaises(ValueError):
            ai_decision(state, 500)


class MatchTests(unittest.TestCase):

    def play_match(self, dice, answers, **options):
        frames = []
        pauses = []
        prompts = []
        inputs = iter(answers)

        def answer(prompt):
            prompts.append(prompt)
            return next(inputs)

        options.setdefault("ai_delay", 0)
        starting_roll = options.pop("starting_roll", 1)
        match = run_match(answer, frames.append, FixedRandom([starting_roll] + dice),
                          sleep_func=pauses.append, **options)
        return match, frames, pauses, prompts

    def test_zero_starts_ai_then_player_after_banking(self):
        match, frames, _, prompts = self.play_match(
            [1, 1, 1, 2, 3, 6] + [1, 2, 3, 4, 6, 6],
            ["", "1", "b", "q"], starting_roll=0)
        self.assertEqual(match.starting_roll, 0)
        self.assertEqual(match.scores, {"Player": 100, "Opponent": 500})
        self.assertIn("Active side: Opponent", frames[0])
        self.assertIn("Press Enter", prompts[0])
        self.assertTrue(all("First-turn roll: 0 (Opponent starts)" in f for f in frames))

    def test_one_starts_player_and_draws_opening_roll_only_once(self):
        source = FixedRandom([1] + [1, 2, 3, 4, 6, 6] + [1, 1, 1, 2, 3, 6])
        inputs = iter(["1", "b", "", "q"])
        frames = []
        match = run_match(lambda prompt: next(inputs), frames.append, source, ai_delay=0)
        self.assertEqual(match.starting_roll, 1)
        self.assertIn("Active side: Player", frames[0])
        self.assertEqual(source.calls, [(0, 1)] + [(1, 6)] * 12)
        self.assertTrue(all("First-turn roll: 1 (Player starts)" in f for f in frames))
        self.assertTrue(all(len(line) == 66 for f in frames for line in f.splitlines()))

    def test_ai_first_bust_passes_turn_to_player(self):
        match, frames, _, _ = self.play_match(
            [2, 3, 3, 4, 6, 6] + [1, 2, 3, 4, 6, 6],
            ["", "q"], starting_roll=0)
        self.assertIn("Opponent BUST", frames[0])
        self.assertIn("Turn: 2", frames[-1])
        self.assertIn("Active side: Player", frames[-1])
        self.assertEqual(match.scores, {"Player": 0, "Opponent": 0})

    def test_ai_starting_turn_can_win_without_player_input(self):
        match, frames, _, prompts = self.play_match(
            [1, 1, 1, 2, 3, 6], [], starting_roll=0, target=500)
        self.assertEqual(match.winner, "Opponent")
        self.assertEqual(match.scores, {"Player": 0, "Opponent": 500})
        self.assertEqual(prompts, [])
        self.assertIn("DEFEAT", frames[-1])

    def test_roll_select_and_bank_are_visible_with_injected_pauses(self):
        match, frames, pauses, prompts = self.play_match(
            [1, 2, 3, 4, 6, 6] + [1, 1, 1, 2, 3, 6],
            ["1", "b", "", "q"], ai_delay=2)
        self.assertEqual(match.scores, {"Player": 100, "Opponent": 500})
        self.assertEqual(pauses, [2, 2, 2])
        self.assertEqual(sum("Select scoring dice" in p for p in prompts), 1)
        rolled = next(f for f in frames if "Opponent rolled" in f)
        selected = next(f for f in frames if "Opponent selects positions" in f)
        decision = next(f for f in frames if "Opponent decision: BANK" in f)
        self.assertLess(frames.index(rolled), frames.index(selected))
        self.assertLess(frames.index(selected), frames.index(decision))
        self.assertIn("Active side: Opponent", rolled)
        self.assertIn("1 2 3: +500", selected)
        # Read the visible text across wrapped rows rather than fixing a line break.
        decision_text = " ".join(line[2:-2].strip() for line in decision.splitlines()
                                 if line.startswith("|"))
        self.assertIn("Turn score 500 >= ambition 500", decision_text)
        markers = next(line for line in selected.splitlines() if "Selected:" in line)
        self.assertEqual(markers.count("^"), 3)
        self.assertTrue(all(len(line) == 66 for line in selected.splitlines()))

    def test_ai_rolls_below_ambition_then_banks_after_hot_dice(self):
        match, frames, pauses, _ = self.play_match(
            [1, 2, 3, 4, 6, 6] + [2, 2, 2, 3, 4, 6] + [3, 3, 3],
            ["1", "b", "", "q"])
        self.assertEqual(match.scores, {"Player": 100, "Opponent": 500})
        self.assertEqual(pauses, [])
        self.assertTrue(any("Opponent decision: ROLL" in f for f in frames))
        self.assertTrue(any("Opponent rolled 3 dice" in f for f in frames))
        hot = next(f for f in frames if "HOT DICE" in f)
        self.assertIn("Unbanked score (at risk): 500", hot)
        self.assertIn("Dice available next: 6", hot)

    def test_repeated_zero_pairs_preserve_points_and_never_open_bank_prompt(self):
        match, frames, _, prompts = self.play_match(
            [1, 2, 3, 4, 6, 6] + [1, 1, 1, 5, 5, 5]
            + [2, 2, 4, 4, 6, 6] * 2 + [1, 1, 1, 5, 5, 5],
            ["1", "b", ""], score_ambition=2500)
        self.assertEqual(match.winner, "Opponent")
        self.assertEqual(match.scores["Opponent"], 2000)
        pair_frames = [f for f in frames if "Phase: ready" in f]
        self.assertEqual(len(pair_frames), 2)
        for frame in pair_frames:
            self.assertIn("THREE PAIRS: +0", frame)
            self.assertIn("Unbanked score (at risk): 1000", frame)
            self.assertIn("Dice available next: 6", frame)
            self.assertNotIn("[B]ank", frame)
        self.assertEqual(sum("[B]ank" in p for p in prompts), 1)
        self.assertTrue(any("wins immediately" in f for f in frames))
        self.assertIn("DEFEAT", frames[-1])

    def test_ai_bust_does_not_take_away_player_banked_points(self):
        match, frames, _, _ = self.play_match(
            [1, 2, 3, 4, 6, 6] + [1, 1, 3, 3, 6, 6] + [2, 3, 4, 6],
            ["1", "b", "", "q"])
        self.assertEqual(match.scores, {"Player": 100, "Opponent": 0})
        bust = next(f for f in frames if "Opponent BUST" in f)
        self.assertIn("Unbanked score (at risk): 0", bust)
        self.assertIn("Player: 100    Opponent: 0", bust)
        self.assertIn("Dice available next: 0", bust)

    def test_player_exact_target_and_overshoot_stop_before_another_ai_turn(self):
        for last_roll, expected in [([2] * 6, 2000), ([1, 2, 3, 4, 5, 6], 2400)]:
            with self.subTest(expected=expected):
                match, frames, _, _ = self.play_match(
                    [1, 2, 3, 4, 5, 6] + [5, 5, 5, 2, 3, 6] + last_roll,
                    ["1 2 3 4 5 6", "b", "", "", "1 2 3 4 5 6", "b"])
                self.assertEqual(match.winner, "Player")
                self.assertEqual(match.scores, {"Player": expected, "Opponent": 500})
                self.assertIn("VICTORY", frames[-1])
                with self.assertRaises(ValueError):
                    match.start_turn()

    def test_opponent_can_win_across_separate_turns(self):
        match, frames, _, _ = self.play_match(
            [1, 2, 3, 4, 6, 6] + [1, 2, 3, 4, 5, 6]
            + [1, 2, 3, 4, 6, 6] + [2] * 6,
            ["1", "b", "", "", "1", "b", ""])
        self.assertEqual(match.winner, "Opponent")
        self.assertEqual(match.scores, {"Player": 200, "Opponent": 2000})
        self.assertIn("DEFEAT", frames[-1])

    def test_unbanked_target_does_not_win_match(self):
        match, frames, _, _ = self.play_match(
            [1, 2, 3, 4, 5, 6] + [2] * 6,
            ["1 2 3 4 5 6", "r", "1 2 3 4 5 6", "q"])
        self.assertIsNone(match.winner)
        self.assertEqual(match.scores["Player"], 0)
        self.assertFalse(any("VICTORY" in f for f in frames))

    def test_ctrl_c_during_ai_pause_exits_without_banking_turn_points(self):
        inputs = iter(["1", "b", ""])
        frames = []

        def interrupted_sleep(seconds):
            raise KeyboardInterrupt()

        match = run_match(lambda prompt: next(inputs), frames.append,
                          FixedRandom([1] + [1, 2, 3, 4, 6, 6] + [1, 1, 1, 2, 3, 6]),
                          sleep_func=interrupted_sleep)
        self.assertIsNone(match.winner)
        self.assertEqual(match.scores, {"Player": 100, "Opponent": 0})
        self.assertIn("Match ended", frames[-1])

    def test_invalid_ai_settings_are_rejected_before_rolling(self):
        for ambition in (0, -1, True, 1.5):
            with self.subTest(ambition=ambition), self.assertRaises(ValueError):
                self.play_match([], [], score_ambition=ambition)
        for delay in (-1, float("nan"), float("inf"), True):
            with self.subTest(delay=delay), self.assertRaises(ValueError):
                self.play_match([], [], ai_delay=delay)

    def test_match_alternates_after_bank_and_bust(self):
        match = MatchState()
        player = match.start_turn()
        with self.assertRaises(ValueError):
            match.finish_turn(player)
        resolve_roll(player, [1, 2, 3, 4, 6, 6], [1])
        player.bank()
        match.finish_turn(player)
        self.assertEqual(match.active_side, "Opponent")
        self.assertEqual(match.turn_number, 2)
        opponent = match.start_turn()
        begin_roll(opponent, [2, 3, 3, 4, 6, 6])
        match.finish_turn(opponent)
        self.assertEqual(match.active_side, "Player")
        self.assertEqual(match.start_turn().match_score, 100)
        self.assertEqual(match.start_turn().unbanked_score, 0)


if __name__ == "__main__":
    unittest.main()
