"""ASCII display and input parsing; game rules live in the core modules."""

import os
import sys
import textwrap


def parse_positions(text):
    """Convert comma- or space-separated text into integer positions."""
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


def read_input(prompt, input_func=input):
    """Treat EOF and Ctrl-C as a request to quit at any input prompt."""
    try:
        return input_func(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _wrap_lines(lines, width):
    """Wrap each panel's text separately, keeping empty rows."""
    rows = []
    for line in lines:
        rows.extend(textwrap.wrap(line, width=width) or [""])
    return rows


def render_gamebar(state, turn_number, roll, selected_positions, message, commands,
                   match_scores=None, active_side="Player", score_ambition=None,
                   first_turn=""):
    """Build one text frame without changing state or calculating rules.

    The battle controller supplies the available commands and result message.
    Display the latest roll even after the core clears its pending roll.
    """
    width = 62
    border = "+" + "-" * (width + 2) + "+"
    lines = [
        "THE KING'S GAMBIT - " + ("PLAYER VS EASY AI" if match_scores is not None
                                  else "SINGLE-PLAYER PRACTICE"),
        f"Turn: {turn_number}    Phase: {state.phase}",
        f"Banked score: {state.match_score} / {state.target}",
        f"Unbanked score (at risk): {state.unbanked_score}",
        f"Dice available next: {state.dice_available}",
        "",
    ]
    if match_scores is not None:
        # Read the current side's live score; the match saves it at turn end.
        scores = dict(match_scores)
        scores[active_side] = state.match_score
        lines[2:2] = [
            f"Active side: {active_side}",
            f"Player: {scores['Player']}    Opponent: {scores['Opponent']}",
            f"Easy AI score ambition: {score_ambition}",
        ]
        if first_turn:
            lines.insert(2, first_turn)
    if roll:
        lines.append("Positions: " + "  ".join(f" {i} " for i in range(1, len(roll) + 1)))
        lines.append("Dice:      " + "  ".join(f"[{die}]" for die in roll))
        # A caret stays under each selected die until the next roll.
        lines.append("Selected:  " + "  ".join(
            " ^ " if i in selected_positions else "   "
            for i in range(1, len(roll) + 1)))
    else:
        lines.append("Dice: waiting for the first roll")
    lines.extend([
        "", f"Result: {message}", f"Actions: {commands}", "",
        "Select by position, e.g. 1 3 5. Q / Ctrl-C exits.",
    ])
    rules = [
        "SCORING RULES", "",
        "Singles 1/5: 100/50. 111: 500; other triples: face x 100.",
        "Extra matching dice: +200 each. Straights: 500/600/1200.",
        "Consecutive pairs: 112233/223344/334455/445566",
        "                  1200 / 1000 / 1100 / 1200.",
        "Ordinary three pairs: select all six for +0 reroll.",
    ]
    # Stack two equal-width boxes so an ordinary 80-column terminal fits them.
    frame = []
    for panel in (rules, lines):
        frame.append(border)
        for row in _wrap_lines(panel, width):
            frame.append("| " + row.ljust(width) + " |")
        frame.append(border)
    return "\n".join(frame)


def show_gamebar(state, turn_number, roll, selected_positions, message,
                 commands, output_func=print, refresh=None, match_scores=None,
                 active_side="Player", score_ambition=None, first_turn=""):
    """Refresh an interactive terminal; keep captured output readable.

    Tests inject an output function, so they never clear the user's terminal.
    Native cls/clear needs no terminal library or cursor-timing assumptions.
    """
    if refresh is None:
        refresh = output_func is print and sys.stdout.isatty()
    if refresh:
        os.system("cls" if os.name == "nt" else "clear")
    output_func(render_gamebar(state, turn_number, roll, selected_positions,
                              message, commands, match_scores, active_side,
                              score_ambition, first_turn))
