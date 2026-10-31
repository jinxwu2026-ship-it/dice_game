"""Functions for rolling ordinary six-sided dice."""

import random

from the_kings_gambit.models import Die, QUALITIES


SYMBOLS = {"basic": "-", "lucky": "♣", "devil": "♠", "angel": "♥",
           "two": "♦", "odd": "▲", "even": "■", "momentum": "↑", "rescue": "↻"}
LETTERS = {"basic": "-", "lucky": "L", "devil": "D", "angel": "A",
           "two": "T", "odd": "O", "even": "E", "momentum": "M", "rescue": "R"}
PRICES = {"basic": 0, "bronze": 200, "silver": 500, "gold": 1200}


def die_weights(die):
    """Initial balance: favoured faces weigh 2/3/4, all others weigh one."""
    if not isinstance(die, Die):
        raise ValueError("expected a Die item")
    return weights_for(die.kind, die.quality)


def weights_for(kind, quality):
    if kind == "rescue" and quality != "silver":
        raise ValueError("rescue dice are always Silver")
    weights = [1] * 6
    if kind in ("basic", "devil", "angel", "momentum", "rescue"):
        return tuple(weights)
    weight = QUALITIES.index(quality) + 2
    faces = {"lucky": (1, 6), "two": (2,), "odd": (1, 3, 5), "even": (2, 4, 6)}
    for face in faces[kind]:
        weights[face - 1] = weight
    return tuple(weights)


def face_distribution(kind, quality):
    """Describe probabilities without creating an item or reserving a unique."""
    weights = weights_for(kind, quality)
    wild_face = {"devil": 1, "angel": 5}.get(kind)
    total = sum(weights)
    return tuple((0 if face == wild_face else face, weight / total)
                 for face, weight in enumerate(weights, 1))


def roll_item(die, random_source=None):
    source = random_source if random_source is not None else random
    weights = die_weights(die)
    ticket = source.randint(1, sum(weights))
    if not isinstance(ticket, int) or isinstance(ticket, bool) or not 1 <= ticket <= sum(weights):
        raise ValueError("random source returned an invalid ticket")
    for face, weight in enumerate(weights, 1):
        ticket -= weight
        if ticket <= 0:
            return 0 if (die.kind, face) in (("devil", 1), ("angel", 5)) else face


def roll_turn_dice(state, random_source=None):
    if not state.is_active or state.phase not in ("ready", "decision"):
        raise ValueError("dice can only be rolled at a ready/decision phase")
    if state.dice is None:
        return roll_dice(state.dice_available, random_source)
    return [roll_item(state.dice[slot], random_source) for slot in state.available_slots]


def die_label(die, symbols=True):
    icon = (SYMBOLS if symbols else LETTERS)[die.kind]
    return icon + ("-" if die.quality == "basic" else die.quality[0].upper())


def roll_first_turn(random_source=None):
    """Roll 0 or 1 once per match: 0 means AI, 1 means Player.

    This opening roll is separate from the six scoring dice.
    """
    if random_source is None:
        random_source = random
    return random_source.randint(0, 1)


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
