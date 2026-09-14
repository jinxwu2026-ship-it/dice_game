"""Command-line display and input for the dice practice mode."""

from the_kings_gambit.battle import resolve_roll
from the_kings_gambit.dice import roll_dice
from the_kings_gambit.models import TurnState
from the_kings_gambit.scoring import is_bust


def parse_positions(text):
    """Convert comma- or space-separated text into integer positions."""
    # Supporting both separators lets the player enter either "1 3 5" or
    # "1, 3, 5" without adding rule logic to the UI.
    cleaned_text = text.replace(",", " ").strip()
    if not cleaned_text:
        raise ValueError("Enter at least one position.")

    positions = []
    for part in cleaned_text.split():
        try:
            positions.append(int(part))
        except ValueError:
            raise ValueError("Positions must be whole numbers.") from None
    return positions


def _show_roll(roll, output_func):
    """Display every die with its one-based selection position."""
    positions = "  ".join(str(position) for position in range(1, len(roll) + 1))
    dice = "  ".join(f"[{die}]" for die in roll)
    output_func(f"Positions: {positions}")
    output_func(f"Dice:      {dice}")


def _ask_for_selection(state, roll, input_func, output_func):
    """Keep asking until the player enters a valid scoring selection."""
    while True:
        text = input_func("Select scoring dice by position (or Q to quit): ").strip()
        if text.lower() == "q":
            return False

        try:
            positions = parse_positions(text)
            # Store the old total so the UI can display how many points this
            # particular selection added.
            old_score = state.unbanked_score
            result = resolve_roll(state, roll, positions)
        except ValueError as error:
            output_func(f"Invalid selection: {error}")
            continue

        points_gained = state.unbanked_score - old_score
        output_func(f"Scored {points_gained} points.")
        output_func(f"Unbanked score: {state.unbanked_score}")
        if result == "hot_dice":
            output_func("HOT DICE! All six dice are available again.")
        return True


def _ask_to_roll_or_bank(state, input_func, output_func):
    """Return 'roll', 'bank', or 'quit' after a valid command."""
    while True:
        command = input_func("[R]oll again, [B]ank, or [Q]uit: ").strip().lower()
        if command in ("r", "roll"):
            return "roll"
        if command in ("b", "bank"):
            state.bank()
            output_func(f"Banked! Match score: {state.match_score}")
            return "bank"
        if command in ("q", "quit"):
            return "quit"
        output_func("Invalid command. Enter R, B, or Q.")


def run_practice(input_func=input, output_func=print, random_source=None):
    """Run repeated single-player turns for manually testing the core rules."""
    output_func("THE KING'S GAMBIT - DICE PRACTICE")
    output_func("Select dice using positions such as: 1 3 5")
    output_func("Only banked points are safe. Q exits practice mode.")

    match_score = 0
    while True:
        state = TurnState(match_score)
        output_func("\n--- New turn ---")

        while state.is_active:
            roll = roll_dice(state.dice_available, random_source)
            output_func(f"\nRolling {state.dice_available} dice...")
            _show_roll(roll, output_func)

            # Bust rolls do not ask the player to choose dice.
            if is_bust(roll):
                resolve_roll(state, roll)
                output_func("BUST! All unbanked points were lost.")
                output_func(f"Match score remains: {state.match_score}")
                break

            if not _ask_for_selection(state, roll, input_func, output_func):
                output_func("Practice ended.")
                return state.match_score

            action = _ask_to_roll_or_bank(state, input_func, output_func)
            if action == "quit":
                output_func("Practice ended.")
                return state.match_score
            if action == "bank":
                break

        match_score = state.match_score
        command = input_func("Press Enter for another turn, or Q to quit: ").strip().lower()
        if command in ("q", "quit"):
            output_func(f"Final banked score: {match_score}")
            return match_score
