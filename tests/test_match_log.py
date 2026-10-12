"""Match records use injected dice and temporary files, never personal logs."""

import io
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from the_kings_gambit.battle import run_match
from the_kings_gambit import main as app


class MatchLogTests(unittest.TestCase):

    def play(self, dice, answers, **options):
        entries = []
        inputs = iter(answers)
        source = Mock()
        source.randint.side_effect = dice
        match = run_match(lambda prompt: next(inputs), lambda frame: None,
                          source, ai_delay=0, log_func=entries.append, **options)
        return match, entries

    def test_complete_match_records_scores_dice_choices_and_winning_reason(self):
        match, entries = self.play(
            [1] + [1, 2, 3, 4, 6, 6] + [1, 1, 1, 5, 5, 5]
            + [2, 2, 4, 4, 6, 6] * 2 + [1, 2, 3, 4, 5, 6],
            ["1", "b", ""], score_ambition=2500)
        text = "".join(entries)
        self.assertEqual(match.winner, "Opponent")
        self.assertIn("First-turn roll: 1 (Player starts)", entries[0])
        self.assertIn("AI ambition: 2500", entries[0])
        self.assertIn("Turn: 2 | Side: Opponent | Event: SELECT", text)
        self.assertIn("Dice: [1, 1, 1, 5, 5, 5] | Selected positions: [1, 2, 3, 4, 5, 6]", text)
        self.assertIn("Current score: 0 | Unbanked: 1000", text)
        self.assertIn("Event: HOT_DICE", text)
        pairs = [e for e in entries if "Event: THREE_PAIRS" in e]
        self.assertEqual(len(pairs), 2)
        self.assertTrue(all("Unbanked: 1000" in e and "+0" in e for e in pairs))
        self.assertIn("Event: ROLL_AGAIN", text)
        self.assertIn("Turn score 1000 < ambition 2500", text)
        self.assertIn("Banking reaches the target and wins immediately", text)
        self.assertIn("Player=100, Opponent=2200", entries[-1])
        self.assertIn("Current score: 2200 | Unbanked: 0", entries[-1])
        self.assertIn("Event: MATCH_END", entries[-1])
        self.assertIn("Winner: Opponent", entries[-1])

    def test_bust_records_at_risk_points_before_and_after_loss(self):
        _, entries = self.play(
            [0] + [1, 1, 3, 3, 6, 6] + [2, 3, 4, 6], ["q"])
        bust_index = next(i for i, e in enumerate(entries) if "Event: BUST" in e)
        self.assertIn("Event: ROLL", entries[bust_index - 1])
        self.assertIn("Unbanked: 200", entries[bust_index - 1])
        self.assertIn("Dice: [2, 3, 4, 6]", entries[bust_index])
        self.assertIn("Lost 200 unbanked points", entries[bust_index])
        self.assertIn("Current score: 0 | Unbanked: 0", entries[bust_index])

    def test_invalid_selection_and_quit_keep_risked_points_distinct(self):
        match, entries = self.play(
            [1] + [1, 2, 3, 4, 6, 6], ["2", "1", "q"])
        invalid = next(e for e in entries if "Event: INVALID_SELECTION" in e)
        self.assertIn("Input: '2'", invalid)
        self.assertIn("Unbanked: 0", invalid)
        self.assertIn("Unbanked: 100", entries[-1])
        self.assertIn("Unbanked points are not saved", entries[-1])
        self.assertEqual(match.scores, {"Player": 0, "Opponent": 0})


class CliLogTests(unittest.TestCase):

    def test_cli_writes_timestamped_utf8_file_and_preserves_previous_record(self):
        started = datetime(2026, 10, 8, 15, 30, 20, 123456, timezone.utc)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary) / "match_logs"
            filename = directory / "2026-10-08_15-30-20_123456.txt"
            calls = []

            def play(**options):
                calls.append(options)
                inputs = iter(["q"])
                source = Mock()
                source.randint.side_effect = [1, 1, 2, 3, 4, 6, 6]
                return run_match(lambda prompt: next(inputs), lambda frame: None,
                                 source, **options)

            output = io.StringIO()
            with patch.object(app, "MATCH_LOG_DIRECTORY", directory), \
                    patch.object(app, "datetime") as clock, \
                    patch.object(app, "run_match", side_effect=play), \
                    patch("sys.argv", ["main.py", "--ai-delay", "0"]), \
                    patch("sys.stdout", output), patch("sys.stderr", io.StringIO()):
                clock.now.return_value.astimezone.return_value = started
                app.main()
                text = filename.read_text(encoding="utf-8")
                self.assertIn("Started: 2026-10-08T15:30:20.123456+00:00", text)
                self.assertIn("Event: MATCH_START", text)
                self.assertIn("Event: MATCH_END", text)
                self.assertIn("Quit", text)
                self.assertIn(str(filename), output.getvalue())
                # Even an identical timestamp must not overwrite an older file.
                with self.assertRaises(SystemExit) as error:
                    app.main()
                self.assertEqual(error.exception.code, 1)
                self.assertEqual(filename.read_text(encoding="utf-8"), text)
            self.assertEqual(len(calls), 2)
            self.assertEqual(list(directory.glob("*.txt")), [filename])

    def test_practice_and_invalid_settings_create_no_record(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary) / "match_logs"
            with patch.object(app, "MATCH_LOG_DIRECTORY", directory), \
                    patch.object(app, "run_practice") as practice, \
                    patch("sys.argv", ["main.py", "--practice"]):
                app.main()
                practice.assert_called_once_with()
            with patch.object(app, "MATCH_LOG_DIRECTORY", directory), \
                    patch("sys.argv", ["main.py", "--ambition", "0"]), \
                    patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    app.main()
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
