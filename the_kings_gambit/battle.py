"""Shared turn rules and deterministic Easy/Normal AI opponents."""

import math
import time

from the_kings_gambit.models import MatchState, TurnState
from the_kings_gambit.dice import roll_dice, roll_first_turn, roll_turn_dice
from the_kings_gambit.scoring import is_bust, selection_action, enumerate_legal_selections, turn_actions
from the_kings_gambit.ui import (parse_positions, read_input, show_gamebar, inspect_dice,
                                present, opponent_presentation)
from the_kings_gambit.ai import (
    GAMMAS, normal_decision, normal_selection, turn_personality, validate_ai_type, ai_rescue,
)


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
    actions = turn_actions(state, roll)  # Validate before changing state.
    state.roll_slots = list(state.available_slots)
    state.last_mapping = {}
    state.last_base = state.last_bonus = 0
    state.hot_dice_faces = {}
    state.current_roll = list(roll)
    if not actions:
        if state.can_rescue:
            state.phase = "rescue"
            return "rescue"
        state.bust()
        return "bust"
    state.phase = "select"
    return "select"


def activate_rescue(state):
    """Spend this battle's shared budget, preserving dice identities and risk."""
    if state.phase not in ("select", "rescue") or not state.can_rescue:
        raise ValueError("rescue requires an available rescue die and an unused charge")
    state.ability_budget["rescue"] -= 1
    state.current_roll = None
    state.phase = "ready"


def resolve_roll(state, roll, selected_positions=None):
    """Resolve a pending roll, or commit and resolve one supplied new roll.

    Invalid choices never change state. A pending roll cannot be replaced.
    Without a pending roll, each call submits a new roll, not leftover dice.
    """
    _validate_roll(state, roll)
    if state.phase == "rescue":
        raise ValueError("use rescue or accept Bust before selecting dice")
    if state.phase == "select" and roll != state.current_roll:
        raise ValueError("select dice from the current roll only")
    actions = turn_actions(state, roll)
    if not actions:
        return begin_roll(state, roll)
    if state.dice is None:
        action = selection_action(roll, selected_positions)
    else:
        if (not isinstance(selected_positions, list) or not selected_positions
                or any(not isinstance(i, int) or isinstance(i, bool) for i in selected_positions)
                or len(set(selected_positions)) != len(selected_positions)):
            raise ValueError("select distinct dice positions")
        wanted = sorted(selected_positions)
        action = next((a for a in actions if a["selected_positions"] == wanted), None)
        if action is None:
            raise ValueError("every selected die must form a legal scoring combination")
    if state.phase != "select":
        begin_roll(state, roll)
    if action["action_type"] == "ordinary_pairs":
        state.available_slots = list(range(6))
        state.held_faces.clear()
        return state.activate_pairs()
    mapping = action.get("wild_values", {})
    state.last_base = action.get("base_score",action["score_delta"])
    state.last_bonus = action.get("bonus_score",0)
    state.last_mapping = {state.available_slots[i - 1] + 1: value for i, value in mapping.items()}
    removed = set(selected_positions)
    for i in selected_positions:
        state.held_faces[state.available_slots[i - 1]] = mapping.get(i, roll[i - 1])
    state.available_slots = [slot for i, slot in enumerate(state.available_slots, 1) if i not in removed]
    result = state.add_selection(action["score_delta"], len(selected_positions))
    if result == "hot_dice":
        state.hot_dice_faces = dict(state.held_faces)
        state.available_slots = list(range(6))
        state.held_faces.clear()
    return result


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


def _validate_score_ambition(score_ambition):
    if not isinstance(score_ambition, int) or isinstance(score_ambition, bool) or score_ambition <= 0:
        raise ValueError("score ambition must be a positive integer")


def _validate_ai_delay(ai_delay):
    if (not isinstance(ai_delay, (int, float)) or isinstance(ai_delay, bool)
            or not math.isfinite(ai_delay) or ai_delay < 0):
        raise ValueError("AI delay must be a finite non-negative number")


def ai_decision(state, score_ambition):
    """Return Bank/Roll and a visible reason, only at a normal decision point."""
    _validate_score_ambition(score_ambition)
    if not state.is_active or state.phase != "decision":
        raise ValueError("AI banking decisions require a positive selection")

    if state.match_score + state.unbanked_score >= state.target:
        return "bank", "Banking reaches the target and wins immediately."
    if state.dice_available == 6:
        return "roll", "Hot Dice: roll all six again before applying the ambition threshold."
    if state.unbanked_score >= score_ambition:
        return "bank", f"Turn score {state.unbanked_score} >= ambition {score_ambition}."
    return "roll", f"Turn score {state.unbanked_score} < ambition {score_ambition}."


def _choose_for_ai(state, roll, personality):
    if personality == "easy":
        if state.dice is not None:
            actions = turn_actions(state, roll)
            return min(actions, key=lambda a: (-a["score_delta"], tuple(a["selected_positions"]))), "highest immediate score."
        return choose_ai_selection(roll), "highest immediate score."
    return normal_selection(state, roll, personality)


def _decide_for_ai(state, score_ambition, personality):
    if personality == "easy":
        return ai_decision(state, score_ambition)
    return normal_decision(state, personality)


def play_ai_turn(state, score_ambition=500, random_source=None, max_rolls=10000,
                 ai_type="easy", other_score=0):
    """Play one fresh AI turn without input, display, sleep or file writes.

    Apply the same transitions and decisions as the interactive opponent.
    Return counters for experiments; the supplied turn state holds the result.
    """
    _validate_score_ambition(score_ambition)
    if (not isinstance(state, TurnState) or not state.is_active
            or state.phase != "ready" or state.unbanked_score != 0):
        raise ValueError("AI needs a fresh active turn")
    if not isinstance(max_rolls, int) or isinstance(max_rolls, bool) or max_rolls <= 0:
        raise ValueError("max_rolls must be a positive integer")
    personality, _ = turn_personality(ai_type, state, other_score)
    stats = {"turns": 1, "rolls": 0, "busts": 0, "banks": 0,
             "banked_points": 0, "hot_dice": 0, "ordinary_pairs": 0}
    if personality != "easy":
        stats[f"{personality}_turns"] = 1
    starting_score = state.match_score
    while state.is_active:
        # A broken random source must not loop forever on zero-point rerolls.
        if stats["rolls"] >= max_rolls:
            raise RuntimeError("AI turn exceeded the roll limit; experiment aborted")
        roll = roll_turn_dice(state, random_source)
        stats["rolls"] += 1
        phase = begin_roll(state, roll)
        if phase == "rescue":
            use, reason = ai_rescue(state)
            if use:
                activate_rescue(state)
                stats["rescues"] = stats.get("rescues",0)+1
                continue
            state.bust()
            phase = "bust"
        if phase == "bust":
            stats["busts"] = 1
            break
        action, _ = _choose_for_ai(state, roll, personality)
        positions = action["selected_positions"]
        result = resolve_roll(state, roll, positions)
        if state.last_bonus:
            stats["momentum_bonus"] = stats.get("momentum_bonus",0)+state.last_bonus
        if result == "ordinary_pairs":
            stats["ordinary_pairs"] += 1
            continue  # No Bank/Roll decision between pairs and their reroll.
        if result == "hot_dice":
            stats["hot_dice"] += 1
        command, _ = _decide_for_ai(state, score_ambition, personality)
        if command == "bank":
            state.bank()
            stats["banks"] = 1
    stats["banked_points"] = state.match_score - starting_score
    return stats


def _run_game(input_func, output_func, random_source, score_ambition,
              ai_delay, sleep_func, target, log_func=None, ai_type="easy", run_context="", rosters=None,
              event_func=None):
    """Use the same turn loop for practice and a single opponent match."""
    if score_ambition is not None:
        _validate_score_ambition(score_ambition)
    validate_ai_type(ai_type)
    _validate_ai_delay(ai_delay)

    match = MatchState(against_ai=score_ambition is not None, target=target, rosters=rosters)
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
        if match.rosters is not None:
            state.other_dice = match.rosters["Player" if is_ai else "Opponent"]
        personality, personality_reason = ("easy", "")
        if is_ai:
            personality, personality_reason = turn_personality(ai_type, state, match.scores["Player"])
        ai_label = "Easy" if ai_type == "easy" else f"Normal ({ai_type})"
        ai_details = "" if ai_type == "easy" else (
            f"Normal personality: {personality if is_ai else ai_type}"
            + (f" (gamma={GAMMAS[personality]})" if is_ai else ""))
        roll = []
        positions = []
        selection_score = 0
        message = "New turn. Only banked points are safe."
        event_name, decision_name = "TURN_START", ""

        def record(event, details=""):
            nonlocal event_name
            event_name = event
            if event_func is not None:
                event_func(dict(event=event,turn=turn_number,side=actor,banked=state.banked_points))
            # Only the CLI supplies a writer. Core calls/tests never create files.
            if log_func is None:
                return
            scores = dict(match.scores)
            scores[actor] = state.match_score
            log_func(
                (f"{run_context}\n" if run_context else "") +
                f"Turn: {turn_number} | Side: {actor} | Event: {event}\n"
                f"Dice: {roll} | Selected positions: {positions} | "
                f"Dice available: {state.dice_available} | Phase: {state.phase}\n"
                f"Banked scores: Player={scores['Player']}, Opponent={scores['Opponent']} | "
                f"Current score: {state.match_score} | Unbanked: {state.unbanked_score}\n"
                + (f"Equipment: {[(d.serial, d.kind, d.quality) for d in state.dice]} | "
                   f"Roll slots: {[i + 1 for i in (state.available_slots if event == 'ROLL' else state.roll_slots)]} | "
                   f"Selected slots: {[state.roll_slots[i-1]+1 for i in positions]} | "
                   f"Wildcard map: {state.last_mapping if event != 'ROLL' else dict()}\n"
                   if state.dice is not None else "") +
                f"Abilities: successes={state.successes}, base={state.last_base if event != 'ROLL' else 0}, "
                f"momentum_bonus={state.last_bonus if event != 'ROLL' else 0}, rescue_left={state.ability_budget['rescue']}\n"
                f"Details: {details}\n\n")

        if turn_number == 1:
            strategy_details = (f"AI ambition: {score_ambition}" if ai_type == "easy"
                                else "Normal uses utility, not ambition.")
            record("MATCH_START", f"{first_turn}; Target: {target}; AI type: {ai_type}; "
                   + strategy_details)
        record("TURN_START", personality_reason)

        def show(commands):
            dialogue, fact = opponent_presentation(event_name,personality,state,positions,decision_name) if is_ai else ("", "")
            show_gamebar(state, turn_number, roll, positions, message,
                         commands, output_func,
                         match_scores=match.scores if match.against_ai else None,
                         active_side=actor, score_ambition=score_ambition,
                         first_turn=first_turn, ai_label=ai_label, ai_details=ai_details,
                         run_context=run_context,
                         actions=turn_actions(state, roll) if state.phase == "select" else [],
                         selection_score=selection_score, dialogue=dialogue,action_fact=fact)

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
                         first_turn=first_turn, ai_label=ai_label, ai_details=ai_details,
                         run_context=run_context)
            return match

        while state.is_active:
            number_of_dice = state.dice_available
            roll = roll_turn_dice(state, random_source)
            positions = []
            selection_score = 0
            record("ROLL", f"Rolled {number_of_dice} dice.")
            # A copied presentation event lets the window animate even a Bust roll.
            present(output_func, "rolling", state=state, roll=roll,
                    active_side=actor, turn_number=turn_number,
                    match_scores=match.scores if match.against_ai else None,
                    first_turn=first_turn, ai_label=ai_label, ai_details=ai_details,
                    selected_positions=[], actions=[], selection_score=0,
                    message=f"Rolling {number_of_dice} dice...")
            risked_points = state.unbanked_score
            phase = begin_roll(state, roll)
            if phase == "rescue":
                message = "No scoring choice. Use R to rescue all remaining dice, or S to accept Bust."
                record("RESCUE_OFFER",message)
                show("R: use rescue | S: accept Bust | Q: quit")
                if is_ai:
                    if not pause():
                        return quit_game()
                    use, reason = ai_rescue(state)
                else:
                    while True:
                        text = read_input("[R]escue, [S] accept Bust, or [Q]uit: ",input_func)
                        if text in ("q","quit"):
                            return quit_game()
                        if inspect_dice(state,text,output_func):
                            continue
                        if text in ("r","rescue","s","skip"):
                            use, reason = text in ("r","rescue"),"Player chooses whether to use rescue."
                            break
                        message = "Enter R to use rescue, S to accept Bust, or Q to quit."
                        show("R: rescue | S: accept Bust | Q: quit")
                if use:
                    activate_rescue(state)
                    message = "Rescue used: rerolling all remaining dice. Earlier turn points kept."
                    record("RESCUE_USED",reason+" "+message)
                    show("Rescue reroll")
                    if not pause():
                        return quit_game()
                    continue
                state.bust()
                phase = "bust"
                record("RESCUE_DECLINED",reason)
            if phase == "bust":
                message = f"{actor} BUST! All unbanked points were lost. Banked score is safe."
                record("BUST", f"Lost {risked_points} unbanked points. Banked score is safe.")
                break

            if is_ai:
                message = f"Opponent rolled {number_of_dice} dice. Choosing a legal selection."
                show("Watch Opponent; Ctrl-C quits")
                if not pause():
                    return quit_game()
                action, selection_reason = _choose_for_ai(state, roll, personality)
                positions = action["selected_positions"]
                old_score = state.unbanked_score
                result = resolve_roll(state, roll, positions)
            else:
                actions = turn_actions(state, roll)
                if any(action["action_type"] == "ordinary_pairs" for action in actions):
                    message += " Optional: select all six for +0 three pairs."
                if state.can_rescue:
                    message += " R: optional rescue reroll (once this battle)."
                show("Select scoring positions, R: rescue if available, or Q")

                # Rejected choices leave the pending roll and scores unchanged.
                while True:
                    text = read_input("Select scoring dice by position (R: rescue if available; Q: quit): ", input_func)
                    if text in ("q", "quit"):
                        return quit_game()
                    if inspect_dice(state, text, output_func):
                        continue
                    if text in ("r","rescue") and state.can_rescue:
                        activate_rescue(state)
                        record("RESCUE_USED","Player rerolls the pending result; earlier points kept.")
                        result = "rescue_reroll"
                        break
                    try:
                        selected = parse_positions(text)
                        if state.dice is not None:
                            if any(slot - 1 not in state.available_slots for slot in selected):
                                raise ValueError("select available fixed slot numbers only")
                            selected = [state.available_slots.index(slot - 1) + 1 for slot in selected]
                        old_score = state.unbanked_score
                        result = resolve_roll(state, roll, selected)
                    except ValueError as error:
                        message = f"Invalid selection: {error}"
                        record("INVALID_SELECTION", f"Input: {text!r}. {error}")
                        show("Select scoring positions, or Q")
                        continue
                    positions = selected
                    break

            if result == "rescue_reroll":
                continue

            points = state.unbanked_score - old_score
            selection_score = points
            if result == "ordinary_pairs":
                message = "THREE PAIRS: +0, earlier turn points kept. Rerolling six dice now."
                if is_ai:
                    message = "Opponent selects all six. " + message
                record("THREE_PAIRS", message + (" " + selection_reason if is_ai else ""))
                show("Immediate six-die reroll (Bank unavailable)")
                if not pause():
                    return quit_game()
                continue

            message = f"Scored {points} points."
            if state.last_bonus:
                message += f" Base {state.last_base}; Momentum +{state.last_bonus}."
            if state.last_mapping:
                message += f" Wildcard conversion: {state.last_mapping}."
            if is_ai:
                choices = " ".join(str(state.roll_slots[position-1] + 1 if state.dice is not None else position)
                                   for position in positions)
                message = f"Opponent selects positions {choices}: +{points}, {selection_reason}"
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
                    command, reason = _decide_for_ai(state, score_ambition, personality)
                    decision_name = command
                    message = f"Opponent decision: {command.upper()}. {reason}"
                    record("DECISION", message)
                    show("Watch Opponent; Ctrl-C quits")
                    if not pause():
                        return quit_game()
                else:
                    command = read_input("[R]oll again, [B]ank, or [Q]uit: ", input_func)
                    if inspect_dice(state, command, output_func):
                        continue
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
              log_func=None, ai_type="easy", run_context="", rosters=None, event_func=None):
    """Play one opponent match; optionally send text events to a writer."""
    return _run_game(input_func, output_func, random_source, score_ambition,
                     ai_delay, sleep_func, target, log_func, ai_type, run_context, rosters, event_func)
