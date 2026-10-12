"""Shared turn rules and a deterministic Easy AI opponent."""

import math
import time

from the_kings_gambit.models import MatchState, TurnState
from the_kings_gambit.dice import roll_dice, roll_first_turn
from the_kings_gambit.scoring import is_bust, selection_action, enumerate_legal_selections
from the_kings_gambit.ui import parse_positions, read_input, show_gamebar


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


def choose_ai_selection(roll):
    """Choose highest points, breaking ties by earliest positional tuple.

    For example, (1, 2) sorts before (1, 3). A legal zero-point ordinary-pair
    action is chosen if it is the only option; no legal actions means bust.
    """
    actions = enumerate_legal_selections(roll)
    if not actions:
        return None
    return min(actions, key=lambda action: (
        -action["score_delta"], tuple(action["selected_positions"])))


def ai_decision(state, score_ambition):
    """Return Bank/Roll and a visible reason, only at a normal decision point."""
    if not isinstance(score_ambition, int) or isinstance(score_ambition, bool) or score_ambition <= 0:
        raise ValueError("score ambition must be a positive integer")
    if not state.is_active or state.phase != "decision":
        raise ValueError("AI banking decisions require a positive selection")

    if state.match_score + state.unbanked_score >= state.target:
        return "bank", "Banking reaches the target and wins immediately."
    if state.unbanked_score >= score_ambition:
        return "bank", f"Turn score {state.unbanked_score} >= ambition {score_ambition}."
    return "roll", f"Turn score {state.unbanked_score} < ambition {score_ambition}."


def _run_game(input_func, output_func, random_source, score_ambition,
              ai_delay, sleep_func, target, log_func=None):
    """Use the same turn loop for practice and a single opponent match."""
    if score_ambition is not None:
        if not isinstance(score_ambition, int) or isinstance(score_ambition, bool) or score_ambition <= 0:
            raise ValueError("score ambition must be a positive integer")
    if (not isinstance(ai_delay, (int, float)) or isinstance(ai_delay, bool)
            or not math.isfinite(ai_delay) or ai_delay < 0):
        raise ValueError("AI delay must be a finite non-negative number")

    match = MatchState(against_ai=score_ambition is not None, target=target)
    first_turn = ""
    if match.against_ai:
        # Choose once, before any scoring dice. Later turns simply alternate.
        match.starting_roll = roll_first_turn(random_source)
        match.active_side = "Opponent" if match.starting_roll == 0 else "Player"
        first_turn = f"First-turn roll: {match.starting_roll} ({match.active_side} starts)"
    while match.winner is None:
        actor = match.active_side
        is_ai = actor == "Opponent"
        turn_number = match.turn_number
        state = match.start_turn()
        roll = []
        positions = []
        message = "New turn. Only banked points are safe."

        def record(event, details=""):
            # Only the CLI supplies a writer. Core calls/tests never create files.
            if log_func is None:
                return
            scores = dict(match.scores)
            scores[actor] = state.match_score
            log_func(
                f"Turn: {turn_number} | Side: {actor} | Event: {event}\n"
                f"Dice: {roll} | Selected positions: {positions} | "
                f"Dice available: {state.dice_available} | Phase: {state.phase}\n"
                f"Banked scores: Player={scores['Player']}, Opponent={scores['Opponent']} | "
                f"Current score: {state.match_score} | Unbanked: {state.unbanked_score}\n"
                f"Details: {details}\n\n")

        if turn_number == 1:
            record("MATCH_START", f"{first_turn}; Target: {target}; AI ambition: {score_ambition}")
        record("TURN_START")

        def show(commands):
            show_gamebar(state, turn_number, roll, positions, message,
                         commands, output_func,
                         match_scores=match.scores if match.against_ai else None,
                         active_side=actor, score_ambition=score_ambition,
                         first_turn=first_turn)

        def pause():
            # Tests supply a recording function instead of actually waiting.
            if is_ai and ai_delay:
                try:
                    sleep_func(ai_delay)
                except KeyboardInterrupt:
                    return False
            return True

        def quit_game():
            match.scores[actor] = state.match_score
            record("MATCH_END", "Quit. Unbanked points are not saved; no winner.")
            label = "Match" if match.against_ai else "Practice"
            show_gamebar(state, turn_number, roll, positions,
                         f"{label} ended. Final banked score: {state.match_score}",
                         "None", output_func,
                         match_scores=match.scores if match.against_ai else None,
                         active_side=actor, score_ambition=score_ambition,
                         first_turn=first_turn)
            return match

        while state.is_active:
            number_of_dice = state.dice_available
            roll = roll_dice(number_of_dice, random_source)
            positions = []
            record("ROLL", f"Rolled {number_of_dice} dice.")
            risked_points = state.unbanked_score
            if begin_roll(state, roll) == "bust":
                message = f"{actor} BUST! All unbanked points were lost. Banked score is safe."
                record("BUST", f"Lost {risked_points} unbanked points. Banked score is safe.")
                break

            if is_ai:
                message = f"Opponent rolled {number_of_dice} dice. Choosing a legal selection."
                show("Watch Opponent; Ctrl-C quits")
                if not pause():
                    return quit_game()
                positions = choose_ai_selection(roll)["selected_positions"]
                old_score = state.unbanked_score
                result = resolve_roll(state, roll, positions)
            else:
                actions = enumerate_legal_selections(roll)
                if any(action["action_type"] == "ordinary_pairs" for action in actions):
                    message += " Optional: select all six for +0 three pairs."
                show("Select scoring positions, or Q")

                # Rejected choices leave the pending roll and scores unchanged.
                while True:
                    text = read_input("Select scoring dice by position (or Q to quit): ", input_func)
                    if text in ("q", "quit"):
                        return quit_game()
                    try:
                        selected = parse_positions(text)
                        old_score = state.unbanked_score
                        result = resolve_roll(state, roll, selected)
                    except ValueError as error:
                        message = f"Invalid selection: {error}"
                        record("INVALID_SELECTION", f"Input: {text!r}. {error}")
                        show("Select scoring positions, or Q")
                        continue
                    positions = selected
                    break

            points = state.unbanked_score - old_score
            if result == "ordinary_pairs":
                message = "THREE PAIRS: +0, earlier turn points kept. Rerolling six dice now."
                if is_ai:
                    message = "Opponent selects all six. " + message
                record("THREE_PAIRS", message)
                show("Immediate six-die reroll (Bank unavailable)")
                if not pause():
                    return quit_game()
                continue

            message = f"Scored {points} points."
            if is_ai:
                choices = " ".join(str(position) for position in positions)
                message = f"Opponent selects positions {choices}: +{points}, highest immediate score."
            if result == "hot_dice":
                message += " HOT DICE! All six dice are available again."
            record("SELECT", f"+{points}. " + message)
            if result == "hot_dice":
                record("HOT_DICE", "All six dice available; unbanked points remain at risk.")
            show("Watch Opponent; Ctrl-C quits" if is_ai else "[R]oll again, [B]ank, or [Q]uit")
            if not pause():
                return quit_game()

            while True:
                if is_ai:
                    command, reason = ai_decision(state, score_ambition)
                    message = f"Opponent decision: {command.upper()}. {reason}"
                    record("DECISION", message)
                    show("Watch Opponent; Ctrl-C quits")
                    if not pause():
                        return quit_game()
                else:
                    command = read_input("[R]oll again, [B]ank, or [Q]uit: ", input_func)
                if command in ("q", "quit"):
                    return quit_game()
                if command in ("b", "bank"):
                    if not is_ai:
                        record("DECISION", "Player chooses BANK.")
                    state.bank()
                    message = f"{actor} Banked! Match score: {state.match_score}"
                    if is_ai:
                        message += " " + reason
                    record("BANK", message)
                    break
                if command in ("r", "roll"):
                    if not is_ai:
                        record("DECISION", "Player chooses ROLL.")
                    record("ROLL_AGAIN", "Continue with available dice; unbanked points stay at risk.")
                    message = "Rolled again. Choose from the new dice."
                    break
                message = "Invalid command. Enter R, B, or Q."
                record("INVALID_COMMAND", f"Input: {command!r}. " + message)
                show("[R]oll again, [B]ank, or [Q]uit")

        match.finish_turn(state)
        if match.winner is not None:
            if not match.against_ai:
                message = f"VICTORY! Practice target reached. Final banked score: {state.match_score}"
            elif match.winner == "Player":
                message = "VICTORY! Player banked enough points to win."
            else:
                message = "DEFEAT! Opponent banked enough points to win."
            record("MATCH_END", f"Winner: {match.winner}. " + message)
            show("Match complete" if match.against_ai else "Practice complete")
            return match

        # This prompt keeps the final Bank/Bust frame visible for as long as
        # the player needs, including after an automatically played AI turn.
        show("Enter: next turn; Q: quit")
        while True:
            command = read_input("Press Enter for another turn, or Q to quit: ", input_func)
            if command in ("q", "quit"):
                return quit_game()
            if command == "":
                break
            message = "Invalid command. Press Enter for another turn, or Q to quit."
            show("Enter: next turn; Q: quit")


def run_practice(input_func=input, output_func=print, random_source=None):
    """Keep the original single-player mode available for rules practice."""
    match = _run_game(input_func, output_func, random_source, None, 0, time.sleep, 2000)
    return match.scores["Player"]


def run_match(input_func=input, output_func=print, random_source=None,
              score_ambition=500, ai_delay=2, sleep_func=time.sleep, target=2000,
              log_func=None):
    """Play one Player/Easy AI match; optionally send text events to a writer."""
    return _run_game(input_func, output_func, random_source, score_ambition,
                     ai_delay, sleep_func, target, log_func)
