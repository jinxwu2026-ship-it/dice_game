"""Tests for deterministic and valid dice rolling."""

import unittest

from the_kings_gambit.dice import roll_dice


class FakeRandom:
    """Return known values so tests never depend on luck."""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        # Each call returns the next prepared value instead of a random value.
        value = self.values.pop(0)
        if value < low or value > high:
            raise AssertionError("test value is outside the requested range")
        return value


class RollDiceTests(unittest.TestCase):

    def test_turn_starts_by_rolling_six_dice(self):
        source = FakeRandom([1, 2, 3, 4, 5, 6])
        self.assertEqual(roll_dice(random_source=source), [1, 2, 3, 4, 5, 6])

    def test_can_roll_only_the_remaining_dice(self):
        source = FakeRandom([6, 2, 5])
        self.assertEqual(roll_dice(3, source), [6, 2, 5])

    def test_rejects_invalid_number_of_dice(self):
        for invalid_number in (0, 7, 2.5, True):
            with self.subTest(invalid_number=invalid_number):
                with self.assertRaises(ValueError):
                    roll_dice(invalid_number)


if __name__ == "__main__":
    unittest.main()
