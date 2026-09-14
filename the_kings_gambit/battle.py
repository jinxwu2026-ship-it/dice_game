"""Coordination for one roll; full matches and AI are not implemented yet."""

from the_kings_gambit.models import TurnState
from the_kings_gambit.scoring import is_bust, score_selection


def resolve_roll(state, roll, selected_positions=None):
    """Apply one roll to a turn and return its result.

    A bust ends the turn immediately. Otherwise, the selected positions must
    form a valid score before the state is changed.
    """
    if not isinstance(state, TurnState):
        raise ValueError("state must be a TurnState")
    if not state.is_active:
        raise ValueError("the turn has already ended")
    if not isinstance(roll, list) or len(roll) != state.dice_available:
        raise ValueError("roll must contain every currently available die")

    # Bust must be checked before asking for a selection because there is no
    # legal selection to make from a bust roll.
    if is_bust(roll):
        state.bust()
        return "bust"

    # score_selection validates everything before add_selection changes state.
    # An invalid choice therefore leaves the turn exactly as it was.
    score = score_selection(roll, selected_positions)
    return state.add_selection(score, len(selected_positions))
