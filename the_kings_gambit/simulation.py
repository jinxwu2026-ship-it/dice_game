"""Headless AI matches and seeded experiments; no personal match logs."""

import argparse
from collections import Counter
from itertools import combinations
import math
import random
from time import perf_counter

from the_kings_gambit.battle import _validate_score_ambition, play_ai_turn
from the_kings_gambit.dice import roll_first_turn
from the_kings_gambit.models import MatchState
from the_kings_gambit.ai import AI_TYPES, GAMMAS, validate_ai_type


def _positive_integer(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def simulate_match(ambition_a=500, ambition_b=500, target=2000,
                   random_source=None, starting_roll=None,
                   max_turns=10000, max_rolls=10000, ai_a="easy", ai_b="easy", rosters=None):
    """Run one match. A uses the Player state slot, B the Opponent slot.

    None draws the usual opening 0/1; experiments can force 1=A or 0=B.
    Safety limits abort rather than inventing a draw or a winner.
    """
    _validate_score_ambition(ambition_a)
    _validate_score_ambition(ambition_b)
    validate_ai_type(ai_a)
    validate_ai_type(ai_b)
    _positive_integer(max_turns, "max_turns")
    _positive_integer(max_rolls, "max_rolls")
    if starting_roll is not None and (
            not isinstance(starting_roll, int) or isinstance(starting_roll, bool)
            or starting_roll not in (0, 1)):
        raise ValueError("starting_roll must be 0, 1 or None")
    match = MatchState(target=target,rosters=rosters)
    if starting_roll is None:
        starting_roll = roll_first_turn(random_source)
    match.starting_roll = starting_roll
    match.active_side = "Player" if starting_roll == 1 else "Opponent"
    labels = {"Player": "A", "Opponent": "B"}
    ambitions = {"Player": ambition_a, "Opponent": ambition_b}
    ai_types = {"Player": ai_a, "Opponent": ai_b}
    stats = {"A": Counter(), "B": Counter()}
    while match.winner is None:
        if match.turn_number > max_turns:
            raise RuntimeError("Match exceeded the turn limit; experiment aborted")
        side = match.active_side
        state = match.start_turn()
        other = "Opponent" if side == "Player" else "Player"
        stats[labels[side]].update(play_ai_turn(
            state, ambitions[side], random_source, max_rolls,
            ai_types[side], match.scores[other]))
        match.finish_turn(state)
    return {
        "winner": labels[match.winner],
        "scores": {labels[side]: score for side, score in match.scores.items()},
        "starting_side": "A" if starting_roll == 1 else "B",
        "turns": match.turn_number,
        "stats": {side: dict(counts) for side, counts in stats.items()},
    }


def run_experiment(games=100, ambition_a=500, ambition_b=500,
                   seed=20261013, target=2000, ai_a="easy", ai_b="easy"):
    """Alternate starters, with a distinct seeded dice stream for each match."""
    _positive_integer(games, "games")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    wins = {"A": 0, "B": 0}
    starts = {"A": 0, "B": 0}
    first_wins = {"A": 0, "B": 0}
    totals = {"A": Counter(), "B": Counter()}
    turn_count = 0
    started = perf_counter()
    for index in range(games):
        result = simulate_match(ambition_a, ambition_b, target,
                                random.Random(seed + index),
                                starting_roll=1 if index % 2 == 0 else 0,
                                ai_a=ai_a, ai_b=ai_b)
        winner = result["winner"]
        first = result["starting_side"]
        wins[winner] += 1
        starts[first] += 1
        if winner == first:
            first_wins[winner] += 1
        turn_count += result["turns"]
        for side in totals:
            totals[side].update(result["stats"][side])
    return {
        "games": games, "seed": seed, "target": target,
        "ambitions": {"A": ambition_a, "B": ambition_b},
        "ai_types": {"A": ai_a, "B": ai_b},
        "wins": wins, "starts": starts, "wins_as_first": first_wins,
        "stats": {side: dict(counts) for side, counts in totals.items()},
        "mean_turns": turn_count / games,
        "elapsed_seconds": perf_counter() - started,
    }


def _win_interval(wins, games):
    """Approximate 95% Wilson interval, including zero or all wins."""
    p = wins / games
    z = 1.96
    denominator = 1 + z * z / games
    center = (p + z * z / (2 * games)) / denominator
    radius = z * math.sqrt(p * (1 - p) / games + z * z / (4 * games * games)) / denominator
    return max(0, center - radius), min(1, center + radius)


def run_round_robin(games=100, seed=2026102600, target=2000):
    """Compare every pair once; games is an even count per pair, not the total.

    Easy stays at ambition 500. Pair j uses seed+j*games through
    seed+(j+1)*games-1, so no pair shares a match seed with another pair.
    """
    _positive_integer(games, "games")
    if games % 2:
        raise ValueError("round-robin games per pair must be even to balance starters")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    results = []
    for index, (ai_a, ai_b) in enumerate(combinations(AI_TYPES, 2)):
        results.append(run_experiment(games=games, seed=seed + index * games,
                                      target=target, ai_a=ai_a, ai_b=ai_b))
    return results


def format_round_robin(results):
    """Show row-versus-column win rates plus the existing detailed reports."""
    matrix = {name: {} for name in AI_TYPES}
    wins = Counter()
    games = Counter()
    for result in results:
        ai_a, ai_b = result["ai_types"]["A"], result["ai_types"]["B"]
        for side, own, other in (("A", ai_a, ai_b), ("B", ai_b, ai_a)):
            matrix[own][other] = result["wins"][side] / result["games"]
            wins[own] += result["wins"][side]
            games[own] += result["games"]
    lines = [
        "AI ROUND ROBIN - Easy ambition 500 and four Normal personalities",
        f"Pairs: {len(results)} | Total matches: {sum(r['games'] for r in results)}",
        "Row win rate against column (no self-play):",
        " " * 14 + " ".join(f"{name:>14}" for name in AI_TYPES),
    ]
    for own in AI_TYPES:
        cells = ["--" if own == other else f"{matrix[own][other]:.1%}"
                 for other in AI_TYPES]
        lines.append(f"{own:<14}" + " ".join(f"{cell:>14}" for cell in cells))
    lines.append("Pool win rates versus the other four profiles (descriptive, not a difficulty guarantee):")
    for name in AI_TYPES:
        lines.append(f"  {name}: {wins[name]}/{games[name]} ({wins[name] / games[name]:.1%})")
    lines.append(f"Total batch elapsed seconds: {sum(r['elapsed_seconds'] for r in results):.3f}")
    lines.append("No parameters changed; pair seed ranges do not overlap within this tournament.")
    lines.extend("\n" + format_report(result) for result in results)
    return "\n".join(lines)


def format_report(result):
    """Summarise experiments as text, not as gameplay frames."""
    games = result["games"]
    lines = [
        "HEADLESS AI EXPERIMENT - base rules 2026-09-21",
        f"Games: {games} | Target: {result['target']} | Seed: {result['seed']}",
        "Match i uses seed+i; starters alternate A/B (odd counts give A one extra start).",
        "No UI, input, sleep or personal match logs.",
    ]
    for side in ("A", "B"):
        wins = result["wins"][side]
        low, high = _win_interval(wins, games)
        starts = result["starts"][side]
        first_wins = result["wins_as_first"][side]
        stats = result["stats"][side]
        turns = stats.get("turns", 0)
        banks = stats.get("banks", 0)
        busts = stats.get("busts", 0)
        bust_rate = busts / turns if turns else 0
        mean_bank = stats.get("banked_points", 0) / banks if banks else 0
        ai_type = result["ai_types"][side]
        label = (f"Easy ambition={result['ambitions'][side]}" if ai_type == "easy"
                 else f"Normal {ai_type} (utility, not win probability)")
        lines.extend([
            f"{side}: {label} | Wins: {wins}/{games} "
            f"({wins / games:.1%}) | Approx. 95% Wilson interval: {low:.1%}-{high:.1%}",
            f"  First: {first_wins}/{starts} wins | "
            f"Second: {wins - first_wins}/{games - starts} wins",
            f"  Turns: {turns} | Rolls: {stats.get('rolls', 0)} | "
            f"Busts: {busts} ({bust_rate:.1%} of turns)",
            f"  Banks: {banks} | Mean points per Bank (excludes Bust): {mean_bank:.1f}",
            f"  Hot Dice: {stats.get('hot_dice', 0)} | Ordinary pairs: {stats.get('ordinary_pairs', 0)}",
        ])
        if ai_type != "easy":
            lines.append("  Personality turns: " + ", ".join(
                f"{name}={stats.get(name + '_turns', 0)}" for name in GAMMAS))
    lines.extend([
        f"Mean turns per match (both sides): {result['mean_turns']:.2f}",
        f"Batch elapsed seconds: {result['elapsed_seconds']:.3f}",
        "This is a preliminary sample, not proof of strength or an optimal ambition.",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Headless Easy/Normal AI matches")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--ambition-a", type=int, default=500)
    parser.add_argument("--ambition-b", type=int, default=500)
    parser.add_argument("--seed", type=int,
                        help="dice seed (pairwise default: 20261013; round-robin: 2026102600)")
    parser.add_argument("--target", type=int, default=2000)
    parser.add_argument("--ai-a", choices=AI_TYPES, default="easy")
    parser.add_argument("--ai-b", choices=AI_TYPES, default="easy")
    parser.add_argument("--round-robin", action="store_true",
                        help="all five profiles, games per pair; Easy fixed at ambition 500")
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else (2026102600 if args.round_robin else 20261013)
    try:
        if args.round_robin:
            if (args.ai_a != "easy" or args.ai_b != "easy"
                    or args.ambition_a != 500 or args.ambition_b != 500):
                parser.error("round-robin fixes all five profiles and Easy 500; omit pairwise AI/ambition options")
            result = run_round_robin(args.games, seed, args.target)
            report = format_round_robin(result)
        else:
            result = run_experiment(args.games, args.ambition_a, args.ambition_b,
                                    seed, args.target, args.ai_a, args.ai_b)
            report = format_report(result)
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(report)


if __name__ == "__main__":
    main()
