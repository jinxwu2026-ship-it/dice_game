"""Application entry point."""

import argparse
import json
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

from the_kings_gambit.battle import run_match, run_practice
from the_kings_gambit.ai import AI_TYPES
from the_kings_gambit import ui
from the_kings_gambit.progression import run_campaign

MATCH_LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "match_logs"


def load_leaderboard():
    """Read completed v1 run scores; personal text logs remain the only storage."""
    entries = []
    try:
        paths = list(MATCH_LOG_DIRECTORY.glob("*.txt"))
    except OSError:
        return entries
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
            blocks = [block for block in content.split("\n\n") if block.strip()]
            if not content.startswith("The King's Gambit - Five-stage run\n"):
                continue
            if not blocks[-1].startswith("Event: RUN_END | "):
                continue
            score_blocks = [block for block in blocks if block.startswith("Event: RUN_SCORE | ")]
            if len(score_blocks) != 1:
                continue
            score = json.loads(next(line.removeprefix("Details: Score: ")
                                   for line in score_blocks[0].splitlines() if line.startswith("Details: Score: ")))
            if not isinstance(score,dict) or type(score.get("version")) is not int or score["version"] != 1:
                continue
            if score.get("status") not in ("victory","defeat"):
                continue
            if not blocks[-1].splitlines()[0].endswith("Status: "+score["status"]):
                continue
            total,rows = score.get("total"),score.get("rows")
            if type(total) is not int or total < 0 or not isinstance(rows,list) or len(rows) != 7:
                continue
            if any(not isinstance(row,dict) or type(row.get("points")) is not int or row["points"] < 0 for row in rows):
                continue
            if sum(row["points"] for row in rows) != total:
                continue
            started = datetime.fromisoformat(next(line[9:] for line in content.splitlines() if line.startswith("Started: ")))
            entries.append(dict(score=total,status=score["status"],started=started,
                                timestamp=started.timestamp(),filename=path.name))
        except (OSError,UnicodeError,ValueError,OverflowError,StopIteration,IndexError):
            continue  # An old, damaged or still-open log must not stop the menu.
    return sorted(entries,key=lambda entry:(-entry["score"],-entry["timestamp"],entry["filename"]))


def play_logged(mode, **options):
    """CLI and window games share one personal-log owner and file lifetime."""
    started_at = datetime.now().astimezone()
    log_path = MATCH_LOG_DIRECTORY / f"{started_at:%Y-%m-%d_%H-%M-%S_%f}.txt"
    with ExitStack() as files:
        log_file = None

        def save_event(entry):
            nonlocal log_file
            if log_file is None:
                MATCH_LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
                log_file = files.enter_context(log_path.open("x", encoding="utf-8"))
                ai_type = options.get("ai_type", "easy")
                label = "Easy" if ai_type == "easy" else f"Normal ({ai_type})"
                title = "Five-stage run" if mode == "run" else f"Player vs {label} AI"
                log_file.write(f"The King's Gambit - {title}\n"
                               f"Started: {started_at.isoformat(timespec='microseconds')}\n\n")
            log_file.write(entry)
            log_file.flush()

        play = run_campaign if mode == "run" else run_match
        result = play(log_func=save_event, **options)
    return result, log_path


def main():
    """Start one match, a fixed five-stage run, or single-player practice."""
    parser = argparse.ArgumentParser(description="The King's Gambit - AI match")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--practice", action="store_true", help="play without an opponent")
    modes.add_argument("--run", action="store_true", help="play the fixed five stages with one extra life")
    modes.add_argument("--gui", action="store_true", help="open the pygame-ce mouse interface")
    parser.add_argument("--ai", choices=AI_TYPES, default="easy", help="opponent personality (default: easy)")
    parser.add_argument("--ambition", type=int, default=500, help="Easy banking threshold; ignored by Normal (default: 500)")
    parser.add_argument("--ai-delay", type=float, default=2, help="seconds per AI action (default: 2)")
    parser.add_argument("--ascii", action="store_true", help="use letter labels instead of Unicode suit symbols")
    args = parser.parse_args()
    ui.USE_SYMBOLS = not args.ascii
    if (args.run or args.gui) and args.ai != "easy":
        parser.error("--run uses fixed stage personalities; --ai selects a single-match opponent")
    if args.gui:
        from the_kings_gambit.battle import _validate_ai_delay, _validate_score_ambition
        try:
            _validate_ai_delay(args.ai_delay)
            _validate_score_ambition(args.ambition)
            from the_kings_gambit.gui import run_gui
            run_gui(score_ambition=args.ambition, ai_delay=args.ai_delay)
        except ImportError as error:
            parser.exit(1, f"GUI dependency unavailable: {error}\nInstall: python -m pip install -r requirements-gui.txt\n")
        except ValueError as error:
            parser.error(str(error))
        return
    if args.practice:
        run_practice()
    else:
        try:
            options = dict(score_ambition=args.ambition, ai_delay=args.ai_delay)
            if not args.run:
                options["ai_type"] = args.ai
            _, log_path = play_logged("run" if args.run else "match", **options)
            label = "Run" if args.run else "Match"
            print(f"{label} log saved: {log_path}")
        except ValueError as error:
            parser.error(str(error))
        except OSError as error:
            parser.exit(1, f"Match log could not be saved: {error}\n")


if __name__ == "__main__":
    main()
