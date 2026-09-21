"""Pure functions for validating and scoring dice selections."""

from collections import Counter
from itertools import combinations


def _validate_dice(dice):
    """Raise ValueError unless dice is a list of one to six valid die values."""
    if not isinstance(dice, list):
        raise ValueError("dice must be provided as a list")
    if len(dice) < 1 or len(dice) > 6:
        raise ValueError("dice must contain between 1 and 6 values")

    for die in dice:
        if not isinstance(die, int) or isinstance(die, bool) or die < 1 or die > 6:
            raise ValueError("each die must be an integer from 1 to 6")


def _score_matching_groups(dice):
    """Score singles and matching groups, or return None if any die cannot score."""
    # Counter changes a list such as [4, 4, 4, 1] into counts like
    # {4: 3, 1: 1}. This makes matching groups straightforward to score.
    counts = Counter(dice)
    score = 0

    for face, count in counts.items():
        if count >= 3:
            # Three 1s have a special base value. Other triples score their
            # face value multiplied by 100.
            base_score = 500 if face == 1 else face * 100
            score += base_score + 200 * (count - 3)
        elif face == 1:
            score += count * 100
        elif face == 5:
            score += count * 50
        else:
            return None

    return score


def calculate_score(selected_dice):
    """Return points, including legal zero for pairs, or None if invalid.

    Every die in the selection must belong to a complete scoring group. This
    prevents a player from setting aside non-scoring dice for a later roll.
    """
    _validate_dice(selected_dice)
    sorted_dice = sorted(selected_dice)

    # Check the six-die straight first because it has its own score and should
    # not be treated as a five-die straight plus one extra die.
    if sorted_dice == [1, 2, 3, 4, 5, 6]:
        return 1200

    counts = Counter(selected_dice)
    if len(counts) == 3 and all(count == 2 for count in counts.values()):
        consecutive_pairs = {
            (1, 2, 3): 1200, (2, 3, 4): 1000,
            (3, 4, 5): 1100, (4, 5, 6): 1200,
        }
        return consecutive_pairs.get(tuple(sorted(counts)), 0)

    straight_options = [
        ([1, 2, 3, 4, 5], 500),
        ([2, 3, 4, 5, 6], 600),
    ]
    for straight, straight_score in straight_options:
        # Work on a copy. Removing a straight from the copy leaves any sixth
        # die available to be checked as a separate scoring die.
        remaining = list(sorted_dice)
        if all(face in remaining for face in straight):
            for face in straight:
                remaining.remove(face)
            extra_score = _score_matching_groups(remaining) if remaining else 0
            if extra_score is not None:
                return straight_score + extra_score

    return _score_matching_groups(sorted_dice)


def selected_dice_from_positions(roll, selected_positions):
    """Return dice at one-based positions after validating the selection."""
    _validate_dice(roll)
    if not isinstance(selected_positions, list) or not selected_positions:
        raise ValueError("select at least one die position")

    # Positions shown to the player start at 1, while Python list indexes start
    # at 0. The set prevents one physical die from being selected twice.
    seen_positions = set()
    selected_dice = []
    for position in selected_positions:
        if not isinstance(position, int) or isinstance(position, bool):
            raise ValueError("each position must be an integer")
        if position < 1 or position > len(roll):
            raise ValueError("selected position is outside the current roll")
        if position in seen_positions:
            raise ValueError("the same die cannot be selected twice")

        seen_positions.add(position)
        selected_dice.append(roll[position - 1])

    return selected_dice


def score_selection(roll, selected_positions):
    """Validate a selection and return its points (ordinary pairs give zero)."""
    # The selected dice are taken directly from this roll. Dice saved during a
    # previous roll are therefore unable to complete a new combination.
    selected_dice = selected_dice_from_positions(roll, selected_positions)
    score = calculate_score(selected_dice)
    if score is None:
        raise ValueError("every selected die must form a scoring group")
    return score


def is_bust(roll):
    """A legal zero-point pair action also prevents a bust."""
    return not enumerate_legal_selections(roll)


def selection_action(roll, selected_positions):
    """Describe a legal choice without changing the roll or any turn state."""
    score = score_selection(roll, selected_positions)
    remaining = len(roll) - len(selected_positions)
    return {
        "selected_positions": sorted(selected_positions),
        "score_delta": score,
        "dice_left": remaining if remaining else 6,
        "hot_dice": remaining == 0,
        "action_type": "ordinary_pairs" if score == 0 else "score",
    }


def enumerate_legal_selections(roll):
    """List legal positional subsets; at most 63 candidates for six dice."""
    _validate_dice(roll)
    actions = []
    for count in range(1, len(roll) + 1):
        for positions in combinations(range(1, len(roll) + 1), count):
            try:
                action = selection_action(roll, list(positions))
            except ValueError:
                continue
            actions.append(action)
    return actions
