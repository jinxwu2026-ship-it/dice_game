"""Single-player turn coordination; no opponent or AI decisions."""

from the_kings_gambit.models import TurnState
from the_kings_gambit.scoring import is_bust, selection_action


def _validate_roll(state, roll):
    if not isinstance(state, TurnState):
        raise ValueError("state must be a TurnState")
    if not state.is_active:
        raise ValueError("the turn has already ended")
    if not isinstance(roll, list) or len(roll) != state.dice_available:
        raise ValueError("roll must contain every currently available die")


def begin_roll(state, roll):
    """Commit a new roll, disabling bank until a positive selection is made."""
    _validate_roll(state, roll)
    if state.phase not in ("ready", "decision"):
        raise ValueError("select from the pending roll before rolling again")
    bust = is_bust(roll)  # Validate values before changing state.
    if bust:
        state.bust()
        return "bust"
    state.current_roll = list(roll)
    state.phase = "select"
    return "select"


def resolve_roll(state, roll, selected_positions=None):
    """Resolve a pending roll, or commit and resolve one supplied new roll.

    Invalid choices never change state. A pending roll cannot be replaced.
    Without a pending roll, each call submits a new roll, not leftover dice.
    """
    _validate_roll(state, roll)
    if state.phase == "select" and roll != state.current_roll:
        raise ValueError("select dice from the current roll only")
    if is_bust(roll):
        state.bust()
        return "bust"
    action = selection_action(roll, selected_positions)
    if state.phase != "select":
        begin_roll(state, roll)
    if action["action_type"] == "ordinary_pairs":
        return state.activate_pairs()
    return state.add_selection(action["score_delta"], len(selected_positions))
