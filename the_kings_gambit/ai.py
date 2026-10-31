"""Normal personalities evaluate turn utility, not whole-match win probability."""

from collections import Counter
from functools import lru_cache
from itertools import combinations_with_replacement
from math import factorial

from the_kings_gambit.models import TurnState
from the_kings_gambit.scoring import (enumerate_legal_selections, legal_actions, turn_actions,
                                    momentum_bonus, MOMENTUM_CAP, MOMENTUM_PER_SUCCESS)
from the_kings_gambit.dice import face_distribution

GAMMAS = {"conservative": 0.5, "neutral": 1.0, "aggressive": 2.0}
AI_TYPES = ("easy", "conservative", "neutral", "aggressive", "composite")
TOLERANCE = 1e-12


def ai_rescue(state):
    """Simple shared policy: protect existing risk, reserve the charge at zero."""
    use = state.phase == "rescue" and state.can_rescue and state.unbanked_score > 0
    return use, ("Use rescue to protect unbanked points." if use else
                 "Keep the rescue charge: no turn points are at risk.")


def validate_ai_type(ai_type):
    if not isinstance(ai_type, str) or ai_type not in AI_TYPES:
        raise ValueError("AI type must be one of: " + ", ".join(AI_TYPES))


def turn_personality(ai_type, state, other_score=0):
    """Choose once at turn start. Fixed personalities never change type."""
    validate_ai_type(ai_type)
    if not isinstance(state, TurnState) or not state.is_active:
        raise ValueError("personality selection requires an active turn")
    other = TurnState(match_score=other_score, target=state.target)
    if not other.is_active:
        raise ValueError("the other side has already won")
    if ai_type != "composite":
        details = "" if ai_type == "easy" else f" Gamma={GAMMAS[ai_type]}."
        return ai_type, f"Fixed personality: {ai_type}." + details
    gap = state.match_score - other_score
    other_need = state.target - other_score
    if other_need <= 250:
        personality, reason = "aggressive", "Opponent needs at most 250 points."
    elif gap <= -600:
        personality, reason = "aggressive", "At least 600 points behind."
    elif other_need <= 500:
        personality, reason = "neutral", "Opponent needs at most 500 points."
    elif gap >= 250:
        personality, reason = "conservative", "At least 250 points ahead."
    else:
        personality, reason = "neutral", "Normal score gap."
    return personality, (f"Composite -> {personality}: {reason} "
                         f"Gap={gap}, other need={other_need}, gamma={GAMMAS[personality]}.")


@lru_cache(maxsize=1)
def _roll_outcomes():
    """Group equivalent rolls, keeping their true probabilities and legal actions."""
    outcomes = [[] for _ in range(7)]
    for number in range(1, 7):
        for dice in combinations_with_replacement(range(1, 7), number):
            permutations = factorial(number)
            for count in Counter(dice).values():
                permutations //= factorial(count)
            probability = permutations / (6 ** number)
            actions = enumerate_legal_selections(list(dice))
            positive = sorted({(a["score_delta"] // 50, a["dice_left"])
                               for a in actions if a["action_type"] == "score"})
            pairs = any(a["action_type"] == "ordinary_pairs" for a in actions)
            outcomes[number].append((probability, positive, pairs))
    return outcomes


@lru_cache(maxsize=128)
def _utility_tables(need, gamma):
    """Solve finite turn utility backwards in 50-point steps, capped at victory.

    Positive selections increase T, so only +0 pairs refer to the same T.
    Their six-die self-loop is solved separately, without an illegal Bank.
    """
    units = (need + 49) // 50
    values = [[0.0] * 7 for _ in range(units + 1)]
    rolls = [[0.0] * 7 for _ in range(units + 1)]
    values[units] = [1.0] * 7
    outcomes = _roll_outcomes()
    # Even with enough points, a pending +0 pair action must roll, risking Bust.
    for number in range(1, 7):
        positive = sum(p for p, actions, _ in outcomes[number] if actions)
        pairs_only = sum(p for p, actions, pairs in outcomes[number] if pairs and not actions)
        rolls[units][number] = positive / (1 - pairs_only)
    for points in range(units - 1, -1, -1):
        bank = (points * 50 / need) ** gamma
        for number in range(1, 7):
            base = 0.0
            pair_choices = []
            for probability, actions, pairs in outcomes[number]:
                best = max((values[min(points + score, units)][left]
                            for score, left in actions), default=0.0)
                if pairs:
                    pair_choices.append((probability, best))
                else:
                    base += probability * best  # Bust has no actions and value 0.
            roll = base
            for _ in range(32):
                updated = base + sum(p * max(best, roll) for p, best in pair_choices)
                if abs(updated - roll) <= TOLERANCE:
                    roll = updated
                    break
                roll = updated
            else:
                raise RuntimeError("Normal utility calculation did not converge")
            rolls[points][number] = roll
            values[points][number] = max(bank, roll)
    return values, rolls


def _validate_normal_state(state, personality, phase):
    if not isinstance(personality, str) or personality not in GAMMAS:
        raise ValueError("resolve a fixed Normal personality before deciding")
    if not isinstance(state, TurnState) or not state.is_active or state.phase != phase:
        raise ValueError(f"Normal requires an active {phase} phase")
    if state.unbanked_score % 50:
        raise ValueError("Normal base-rule turn points must be multiples of 50")


def normal_selection(state, roll, personality):
    """Return a legal action and an explanation without changing the turn."""
    _validate_normal_state(state, personality, "select")
    if roll != state.current_roll:
        raise ValueError("select from the pending roll only")
    actions = turn_actions(state, roll)
    need = state.target - state.match_score
    winning = [a for a in actions if a["action_type"] == "score"
               and state.unbanked_score + a["score_delta"] >= need]
    if winning:
        action = min(winning, key=lambda a: tuple(a["selected_positions"]))
        return action, "This selection allows an immediate winning Bank."
    if not actions:
        raise ValueError("a bust must be resolved before AI selection")
    if state.dice is not None and any(d.kind != "basic" for d in state.dice):
        return _item_selection(state, actions, personality)
    values, rolls = _utility_tables(need, GAMMAS[personality])
    units = len(values) - 1
    evaluated = []
    for action in actions:
        if action["action_type"] == "ordinary_pairs":
            value = rolls[min(state.unbanked_score // 50, units)][6]
        else:
            points = (state.unbanked_score + action["score_delta"]) // 50
            value = values[min(points, units)][action["dice_left"]]
        evaluated.append((value, action))
    best = max(value for value, _ in evaluated)
    action = min((a for value, a in evaluated if best - value <= TOLERANCE),
                 key=lambda a: tuple(a["selected_positions"]))
    reason = (f"Normal {personality}: expected turn utility={best:.6f} (not win probability); "
              f"+{action['score_delta']}, next dice={action['dice_left']}.")
    return action, reason


def normal_decision(state, personality):
    """Bank on ties or when winning; otherwise compare expected turn utilities."""
    _validate_normal_state(state, personality, "decision")
    need = state.target - state.match_score
    if state.unbanked_score >= need:
        return "bank", "Banking reaches the target and wins immediately."
    if state.dice is not None and any(d.kind != "basic" for d in state.dice):
        bank = (state.unbanked_score / need) ** GAMMAS[personality]
        roll = _item_roll_value(_signature(state, state.available_slots),
                                state.unbanked_score, need, GAMMAS[personality],
                                state.successes,state.can_rescue)
        return ("roll" if roll > bank + TOLERANCE else "bank"), (
            f"Weighted one-roll lookahead: Bank utility={bank:.6f}, Roll={roll:.6f}; "
            "not a win probability. Future decisions are replanned.")
    _, rolls = _utility_tables(need, GAMMAS[personality])
    bank = (state.unbanked_score / need) ** GAMMAS[personality]
    roll = rolls[state.unbanked_score // 50][state.dice_available]
    command = "roll" if roll > bank + TOLERANCE else "bank"
    return command, (f"Normal {personality}: Bank utility={bank:.6f}, "
                     f"Roll utility={roll:.6f} (not win probability).")


def _signature(state, slots):
    return tuple(sorted((state.dice[i].kind, state.dice[i].quality) for i in slots))


@lru_cache(maxsize=8192)
def _best_roll_score(roll):
    wild = tuple(i + 1 for i, value in enumerate(roll) if value == 0)
    actions = legal_actions(list(roll), wild)
    positive = [a["score_delta"] for a in actions if a["score_delta"] > 0]
    return max(positive) if positive else -1 if actions else 0


@lru_cache(maxsize=256)
def _item_score_distribution(signature):
    """Convolve actual weighted dice; group equivalent multisets, not identities.

    This horizon ends by banking after the next positive roll, so identities
    after that selection do not enter this particular forecast.
    """
    outcomes = {(): 1.0}
    for kind, quality in signature:
        updated = {}
        for values, probability in outcomes.items():
            for face, chance in face_distribution(kind, quality):
                key = tuple(sorted(values + (face,)))
                updated[key] = updated.get(key, 0) + probability * chance
        outcomes = updated
    scores = {}
    for values, probability in outcomes.items():
        score = _best_roll_score(values)
        scores[score] = scores.get(score, 0) + probability
    pair_loop = scores.pop(-1, 0)
    if pair_loop >= 1:
        raise RuntimeError("pair-only forecast cannot terminate")
    return tuple((score, probability / (1 - pair_loop))
                 for score, probability in sorted(scores.items()))


@lru_cache(maxsize=256)
def _effect_score_distribution(signature, successes):
    """Keep Momentum identities while grouping equivalent weighted outcomes."""
    outcomes = {(): 1.0}
    for kind, quality in signature:
        updated = {}
        for values, probability in outcomes.items():
            for face, chance in face_distribution(kind,quality):
                key = tuple(sorted(values+((face,kind == "momentum"),)))
                updated[key] = updated.get(key,0)+probability*chance
        outcomes = updated
    scores = {}
    for tagged, probability in outcomes.items():
        roll = [face for face,is_momentum in tagged]
        wild = tuple(i+1 for i,face in enumerate(roll) if face == 0)
        actions = legal_actions(roll,wild)
        values = [a["score_delta"] + (momentum_bonus(successes) if any(
            tagged[i-1][1] for i in a["selected_positions"]) else 0)
            for a in actions if a["action_type"] == "score"]
        best = max(values) if values else -1 if actions else 0
        scores[best] = scores.get(best,0)+probability
    pair_loop = scores.pop(-1,0)
    return tuple((score,p/(1-pair_loop)) for score,p in scores.items())


def _item_roll_value(signature, risk, need, gamma, successes=0, rescue=False):
    capped_count = min(successes,(MOMENTUM_CAP+MOMENTUM_PER_SUCCESS-1)//MOMENTUM_PER_SUCCESS)
    distribution = (_effect_score_distribution(signature,capped_count)
                    if any(kind == "momentum" for kind,quality in signature) else
                    _item_score_distribution(signature))
    value = sum(p*(min(risk+score,need)/need)**gamma for score,p in distribution if score > 0)
    if rescue and risk > 0 and any(kind == "rescue" for kind,quality in signature):
        value *= 1+sum(p for score,p in distribution if score == 0)
    return value


def _item_selection(state, actions, personality):
    """Deterministic finite lookahead for heterogeneous dice, with exact weights.

    shortcut: only one future positive roll is valued, extend the horizon if
    cross-play shows poor choices; the original all-basic DP stays unchanged.
    """
    need, gamma = state.target - state.match_score, GAMMAS[personality]
    evaluated = []
    for action in actions:
        risk = state.unbanked_score + action["score_delta"]
        removed = set(action["selected_positions"])
        slots = [slot for i, slot in enumerate(state.available_slots, 1) if i not in removed]
        if not slots:
            slots = list(range(6))
        roll = _item_roll_value(_signature(state, slots), risk, need, gamma,
                                state.successes+int(action["action_type"] == "score"),
                                state.ability_budget["rescue"] > 0)
        bank = (min(risk, need) / need) ** gamma
        value = roll if action["action_type"] == "ordinary_pairs" else max(bank, roll)
        evaluated.append((value, action))
    best = max(value for value, _ in evaluated)
    action = min((a for value, a in evaluated if best - value <= TOLERANCE),
                 key=lambda a: tuple(a["selected_positions"]))
    return action, (f"Normal {personality}: weighted one-roll lookahead utility={best:.6f}; "
                    "not a win probability.")
