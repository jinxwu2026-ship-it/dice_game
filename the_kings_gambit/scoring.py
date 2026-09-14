"""Pure functions for validating and scoring dice selections."""

from collections import Counter


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
    """Score singles and matching groups, or return 0 if any die cannot score."""
    # Counter changes a list such as [4, 4, 4, 1] into counts like
    # {4: 3, 1: 1}. This makes matching groups straightforward to score.
    counts = Counter(dice)
    score = 0

    for face, count in counts.items():
        if count >= 3:
            # Three 1s have a special base value. Other triples score their
            # face value multiplied by 100.
            base_score = 1000 if face == 1 else face * 100
            # Every die after the third doubles the whole matching-group score.
            score += base_score * (2 ** (count - 3))
        elif face == 1:
            score += count * 100
        elif face == 5:
            score += count * 50
        else:
            return 0

    return score


def calculate_score(selected_dice):
    """Return the selected dice's score, or 0 when the selection is invalid.

    Every die in the selection must belong to a complete scoring group. This
    prevents a player from setting aside non-scoring dice for a later roll.
    """
    _validate_dice(selected_dice)
    sorted_dice = sorted(selected_dice)

    # Check the six-die straight first because it has its own score and should
    # not be treated as a five-die straight plus one extra die.
    if sorted_dice == [1, 2, 3, 4, 5, 6]:
        return 1500

    straight_options = [
        ([1, 2, 3, 4, 5], 500),
        ([2, 3, 4, 5, 6], 750),
    ]
    for straight, straight_score in straight_options:
        # Work on a copy. Removing a straight from the copy leaves any sixth
        # die available to be checked as a separate scoring die.
        remaining = list(sorted_dice)
        if all(face in remaining for face in straight):
            for face in straight:
                remaining.remove(face)
            extra_score = _score_matching_groups(remaining) if remaining else 0
            if not remaining or extra_score > 0:
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
    """Validate a selection from one roll and return its positive score."""
    # The selected dice are taken directly from this roll. Dice saved during a
    # previous roll are therefore unable to complete a new combination.
    selected_dice = selected_dice_from_positions(roll, selected_positions)
    score = calculate_score(selected_dice)
    if score == 0:
        raise ValueError("every selected die must form a scoring group")
    return score


def is_bust(roll):
    """Return True when the current roll contains no possible scoring choice."""
    _validate_dice(roll)
    counts = Counter(roll)

    # A single 1 or 5 can always be selected. Without one of those, only a
    # matching group of at least three dice can prevent a bust.
    if 1 in counts or 5 in counts:
        return False
    return not any(count >= 3 for count in counts.values())
