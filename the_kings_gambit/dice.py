"""Functions for rolling ordinary six-sided dice."""

import random


def roll_dice(number_of_dice=6, random_source=None):
    """Return a list containing ``number_of_dice`` random values from 1 to 6.

    ``random_source`` can be replaced in tests by any object that provides a
    ``randint(low, high)`` method.
    """
    if not isinstance(number_of_dice, int) or isinstance(number_of_dice, bool):
        raise ValueError("number_of_dice must be an integer")
    if number_of_dice < 1 or number_of_dice > 6:
        raise ValueError("number_of_dice must be between 1 and 6")

    # The real game uses Python's random module. Tests pass in a fake object
    # so that they can choose the exact dice results.
    if random_source is None:
        random_source = random

    dice = []
    # randint includes both end values, so this produces values from 1 to 6.
    for _ in range(number_of_dice):
        dice.append(random_source.randint(1, 6))
    return dice

# test function for rolling dice without validation, useful for testing purposes
# def roll_dice_test(number_of_dice=6, random_source=None):
#     """Return a list containing ``number_of_dice`` random values from 1 to 6.

#     This function is intended for testing purposes and does not perform any
#     validation on the input parameters.
#     """
#     if random_source is None:
#         random_source = random

#     return [random_source.randint(1, 6) for _ in range(number_of_dice)]

# count = int(input("Enter the number of dice to roll (1-6): "))
# if count < 1 or count > 6:
#     print("Invalid number of dice. Please enter a number between 1 and 6.")
# else:
#     result = roll_dice_test(count)
#     print(f"Rolled {count} dice: {result}")
