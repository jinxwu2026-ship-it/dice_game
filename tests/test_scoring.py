"""Tests for scoring, selection validation, busts, and turn state."""

import unittest

from the_kings_gambit.battle import resolve_roll
from the_kings_gambit.models import TurnState
from the_kings_gambit.scoring import calculate_score, is_bust, score_selection


class ScoringTests(unittest.TestCase):

    def test_single_ones_and_fives_score(self):
        self.assertEqual(calculate_score([1]), 100)
        self.assertEqual(calculate_score([5]), 50)
        self.assertEqual(calculate_score([1, 5]), 150)

    def test_every_three_of_a_kind_score(self):
        expected_scores = {1: 1000, 2: 200, 3: 300, 4: 400, 5: 500, 6: 600}
        for face, expected_score in expected_scores.items():
            with self.subTest(face=face):
                self.assertEqual(calculate_score([face, face, face]), expected_score)

    def test_four_to_six_of_a_kind_double_for_each_extra_die(self):
        base_scores = {1: 1000, 2: 200, 3: 300, 4: 400, 5: 500, 6: 600}
        for face, base_score in base_scores.items():
            for count in (4, 5, 6):
                with self.subTest(face=face, count=count):
                    expected = base_score * (2 ** (count - 3))
                    self.assertEqual(calculate_score([face] * count), expected)

    def test_straights_score(self):
        cases = [
            ([1, 2, 3, 4, 5], 500),
            ([2, 3, 4, 5, 6], 750),
            ([1, 2, 3, 4, 5, 6], 1500),
        ]
        for dice, expected in cases:
            with self.subTest(dice=dice):
                self.assertEqual(calculate_score(dice), expected)

    def test_independent_scoring_groups_can_be_combined(self):
        roll = [1, 4, 4, 4, 5, 6]
        self.assertEqual(score_selection(roll, [1, 2, 3, 4, 5]), 550)

    def test_player_does_not_have_to_select_every_scoring_die(self):
        roll = [1, 5, 2, 3, 4, 6]
        self.assertEqual(score_selection(roll, [1]), 100)

    def test_five_die_straight_can_include_one_extra_scoring_die(self):
        self.assertEqual(calculate_score([1, 1, 2, 3, 4, 5]), 600)
        self.assertEqual(calculate_score([2, 3, 4, 5, 5, 6]), 800)

    def test_non_scoring_and_incomplete_groups_are_invalid(self):
        invalid_selections = [[2], [3, 3], [4, 6], [2, 2, 5]]
        for selection in invalid_selections:
            with self.subTest(selection=selection):
                self.assertEqual(calculate_score(selection), 0)

    def test_selection_uses_positions_from_current_roll_only(self):
        roll = [4, 4, 1, 2, 5, 6]
        self.assertEqual(score_selection(roll, [3, 5]), 150)
        with self.assertRaises(ValueError):
            score_selection(roll, [1, 2, 7])

    def test_dice_from_separate_rolls_cannot_complete_a_group(self):
        # Each roll is checked independently. The two 4s from the first roll
        # cannot be combined with the 4 from the second roll.
        first_roll = [4, 4, 1, 2, 5, 6]
        second_roll = [4, 2, 3]
        with self.assertRaises(ValueError):
            score_selection(first_roll, [1, 2])
        with self.assertRaises(ValueError):
            score_selection(second_roll, [1])

    def test_duplicate_empty_and_non_integer_positions_are_rejected(self):
        roll = [1, 2, 3, 4, 5, 6]
        invalid_positions = [[], [1, 1], [0], [7], ["1"], [True]]
        for positions in invalid_positions:
            with self.subTest(positions=positions):
                with self.assertRaises(ValueError):
                    score_selection(roll, positions)

    def test_malformed_dice_are_rejected(self):
        invalid_dice = [[], [0], [7], [True], [1.5], "1, 5", [1] * 7]
        for dice in invalid_dice:
            with self.subTest(dice=dice):
                with self.assertRaises(ValueError):
                    calculate_score(dice)


class BustTests(unittest.TestCase):

    def test_roll_without_any_scoring_choice_is_a_bust(self):
        self.assertTrue(is_bust([2, 3, 3, 4, 6, 6]))

    def test_single_scoring_die_prevents_a_bust(self):
        self.assertFalse(is_bust([2, 3, 4, 5, 6, 6]))

    def test_complete_group_prevents_a_bust(self):
        self.assertFalse(is_bust([2, 2, 2, 3, 4, 6]))

    def test_bust_loses_unbanked_points_but_not_match_score(self):
        state = TurnState(match_score=300)
        resolve_roll(state, [1, 5, 2, 3, 4, 6], [1, 2])
        result = resolve_roll(state, [2, 3, 3, 4], None)
        self.assertEqual(result, "bust")
        self.assertEqual(state.unbanked_score, 0)
        self.assertEqual(state.match_score, 300)
        self.assertFalse(state.is_active)
        self.assertEqual(state.dice_available, 0)


class HotDiceAndBankingTests(unittest.TestCase):

    def test_remaining_dice_decrease_after_a_selection(self):
        state = TurnState()
        result = resolve_roll(state, [1, 5, 2, 3, 4, 6], [1, 2])
        self.assertEqual(result, "scored")
        self.assertEqual(state.unbanked_score, 150)
        self.assertEqual(state.dice_available, 4)

    def test_hot_dice_restore_six_and_preserve_unbanked_score(self):
        state = TurnState()
        result = resolve_roll(state, [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result, "hot_dice")
        self.assertEqual(state.unbanked_score, 1500)
        self.assertEqual(state.dice_available, 6)
        self.assertTrue(state.is_active)

    def test_hot_dice_can_happen_after_several_rolls(self):
        state = TurnState()
        # Score three dice, then score all three remaining dice. Using all six
        # across the turn activates Hot Dice and makes six available again.
        resolve_roll(state, [2, 2, 2, 3, 4, 6], [1, 2, 3])
        result = resolve_roll(state, [1, 5, 5], [1, 2, 3])
        self.assertEqual(result, "hot_dice")
        self.assertEqual(state.unbanked_score, 400)
        self.assertEqual(state.dice_available, 6)

    def test_bust_after_hot_dice_loses_the_whole_turn_score(self):
        state = TurnState(match_score=400)
        resolve_roll(state, [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        resolve_roll(state, [2, 3, 3, 4, 6, 6], None)
        self.assertEqual(state.unbanked_score, 0)
        self.assertEqual(state.match_score, 400)

    def test_banking_transfers_all_unbanked_points_and_ends_turn(self):
        state = TurnState(match_score=300)
        resolve_roll(state, [1, 4, 4, 4, 5, 6], [1, 2, 3, 4, 5])
        state.bank()
        self.assertEqual(state.match_score, 850)
        self.assertEqual(state.unbanked_score, 0)
        self.assertFalse(state.is_active)

    def test_ended_turn_rejects_more_state_changes(self):
        state = TurnState()
        resolve_roll(state, [1, 2, 3, 4, 6, 6], [1])
        state.bank()
        with self.assertRaises(ValueError):
            state.add_selection(50, 1)
        with self.assertRaises(ValueError):
            state.bust()

    def test_roll_must_match_the_number_of_available_dice(self):
        state = TurnState()
        resolve_roll(state, [1, 5, 2, 3, 4, 6], [1, 2])
        with self.assertRaises(ValueError):
            resolve_roll(state, [1, 5, 2], [1])

    def test_invalid_selection_does_not_change_turn_state(self):
        state = TurnState(match_score=200)
        with self.assertRaises(ValueError):
            resolve_roll(state, [3, 3, 4, 4, 5, 6], [1, 2])
        self.assertEqual(state.match_score, 200)
        self.assertEqual(state.unbanked_score, 0)
        self.assertEqual(state.dice_available, 6)
        self.assertTrue(state.is_active)


if __name__ == "__main__":
    unittest.main()
