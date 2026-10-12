"""Application entry point."""

import argparse
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

from the_kings_gambit.battle import run_match, run_practice

MATCH_LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "match_logs"


def main():
    """Start one opponent match, or opt into the original practice mode."""
    parser = argparse.ArgumentParser(description="The King's Gambit - Easy AI match")
    parser.add_argument("--practice", action="store_true", help="play without an opponent")
    parser.add_argument("--ambition", type=int, default=500, help="AI banking threshold (default: 500)")
    parser.add_argument("--ai-delay", type=float, default=2, help="seconds per AI action (default: 2)")
    args = parser.parse_args()
    if args.practice:
        run_practice()
    else:
        try:
            started_at = datetime.now().astimezone()
            log_path = MATCH_LOG_DIRECTORY / f"{started_at:%Y-%m-%d_%H-%M-%S_%f}.txt"
            with ExitStack() as files:
                log_file = None

                def save_event(entry):
                    nonlocal log_file
                    # Open only after validation and the first actual game event.
                    # Tests using run_match directly have no writer and no files.
                    if log_file is None:
                        MATCH_LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
                        log_file = files.enter_context(log_path.open("x", encoding="utf-8"))
                        log_file.write(f"The King's Gambit - Player vs Easy AI\n"
                                       f"Started: {started_at.isoformat(timespec='microseconds')}\n\n")
                    log_file.write(entry)
                    log_file.flush()  # Keep earlier actions if the game is interrupted.

                run_match(score_ambition=args.ambition, ai_delay=args.ai_delay,
                          log_func=save_event)
            print(f"Match log saved: {log_path}")
        except ValueError as error:
            parser.error(str(error))
        except OSError as error:
            parser.exit(1, f"Match log could not be saved: {error}\n")


if __name__ == "__main__":
    main()
