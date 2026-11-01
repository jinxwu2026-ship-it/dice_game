"""ASCII display and input parsing; game rules live in the core modules."""

import os
import sys
import textwrap
import unicodedata

from the_kings_gambit.dice import die_label, face_distribution
from the_kings_gambit.scoring import MOMENTUM_PER_SUCCESS, MOMENTUM_CAP

USE_SYMBOLS = True
ENCOUNTER_STORIES = (
    ("Tavern Gambler", "At the tavern, the first gambler wagers a place on the road."),
    ("Road Warden", "The road warden measures every risk before letting you pass."),
    ("Wild Challenger", "A reckless challenger blocks the path to the dragon's realm."),
    ("Hoard Keeper", "The hoard keeper guards the final approach to the lair."),
    ("The Dragon", "The dragon sets a golden die on the table. This wager has no second chance."),
)


def run_story(run):
    if run.status == "victory":
        return "The dragon yields. The kingdom's golden dice are free again."
    if run.status == "defeat":
        return "The dragon claims the final wager." if run.encounter_index == 4 else "Your road to the hoard ends here."
    if run.history and run.history[-1]["hp_before"] > run.history[-1]["hp_after"]:
        return "The ward cracks. You escape and press on."
    return "The road to the dragon's hoard lies ahead."


def event_story(screen, run):
    if screen == "wager":
        return ENCOUNTER_STORIES[run.encounter_index][1]
    if screen.startswith("guess"):
        return "A travelling trickster offers a wager: claim your prize, or tempt fortune again."
    return {"spinner":"At the crossroads, a wheel tests your fortune.",
            "shop":"The last merchant before the dragon's lair opens their chest.",
            "reward":"Choose what to carry on the road to the hoard.",
            "run_summary":run_story(run)}.get(screen, "")


def present(output_func, screen, **data):
    """An optional structured display; ordinary print callbacks stay unchanged."""
    if callable(getattr(type(output_func), "present", None)):
        output_func.present(screen, **data)
        return True
    return False


def opponent_presentation(event, personality, state, positions=(), command=""):
    """Short deterministic dialogue and facts, based on supplied real events."""
    if event in ("BUST", "RESCUE_DECLINED"):
        return (("I pushed my luck too far." if state.lost_score else "Nothing this time."),
                f"BUST · Lost {state.lost_score}")
    if event == "RESCUE_USED":
        return "Not yet. One more chance.","Rescue used · 0 left this battle"
    if event == "RESCUE_OFFER":
        return "Can I save this throw?",f"At risk {state.unbanked_score} · Rescue available"
    if event in ("BANK", "MATCH_END") and state.outcome == "bank":
        line = "That settles it." if state.has_won else {
            "conservative":"Enough. I'll keep these.", "aggressive":"A fine haul. Mine!",
            "neutral":"A fair haul. I'll take it.", "easy":"I'll keep what I've got."}.get(personality,"I'll take it.")
        return line,f"Banked {state.banked_points} · Total {state.match_score}"
    if event == "DECISION":
        if command == "bank":
            return "Time to collect.",f"Choosing Bank · {state.unbanked_score} at risk"
        return ({"conservative":"One more, carefully.","aggressive":"There's more on this table."}.get(
            personality,"I'll try another throw."),f"Rolling {state.dice_available} dice · Risk {state.unbanked_score}")
    if event in ("SELECT","HOT_DICE"):
        points = state.last_base+state.last_bonus
        line = "Patience pays off!" if state.last_bonus else "Now that's a fine throw!" if points >= 500 else "These will do."
        chosen = ", ".join(str(state.roll_slots[i-1]+1) for i in positions)
        return line,f"Selected {chosen} · +{points}" + (f" (Momentum +{state.last_bonus})" if state.last_bonus else "")
    if event == "THREE_PAIRS":
        return "Back to six. Let's try again.","Three pairs · +0 · Earlier points kept"
    return "Let's see what the dice bring.",f"Rolled {len(state.roll_slots)} dice"


def die_effect_text(die):
    if die.kind == "momentum":
        return f"Score it: +{MOMENTUM_PER_SUCCESS} per earlier success (max +{MOMENTUM_CAP}). Shared bonus; Hot Dice keeps count."
    if die.kind == "rescue":
        return "While available: reroll all remaining dice once per battle. Max one; no merge/upgrade."
    if die.kind in ("devil","angel"):
        return f"{1 if die.kind == 'devil' else 5} becomes wild for 3-6 matches or 5/6 straights. No singles/pairs."
    if die.kind == "basic":
        return "Fair six-sided die."
    odds = face_distribution(die.kind,die.quality)
    lowest = min(chance for _,chance in odds)
    faces = "/".join(str(face) for face,chance in odds if chance > lowest)
    return f"Favors {faces}. Higher quality strengthens this bias; normal scoring."


def symbols_enabled():
    if not USE_SYMBOLS:
        return False
    try:
        "♣♠♥♦▲■↑↻".encode(sys.stdout.encoding or "utf-8")
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def display_width(text):
    # Ambiguous symbols use one column in the default terminal layout.
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1
               for c in text)


def _pad(text, width):
    return text + " " * max(0, width - display_width(text))


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
        if display_width(line) == len(line):
            rows.extend(textwrap.wrap(line, width=width) or [""])
            continue
        current = ""
        for word in line.split():
            if current and display_width(current + " " + word) > width:
                rows.append(current)
                current = ""
            while display_width(word) > width:
                part = ""
                while word and display_width(part + word[0]) <= width:
                    part, word = part + word[0], word[1:]
                rows.append(part)
            current += (" " if current else "") + word
        rows.append(current)
    return rows


def show_panel(lines, output_func=print, view=None):
    """Render a progression screen; the caller owns all game decisions."""
    if view is not None and present(output_func, **view):
        return
    if output_func is print and sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    if not symbols_enabled():
        replacements = str.maketrans("♣♠♥♦▲■↑↻", "LDATOEMR")
        lines = [line.translate(replacements) for line in lines]
    border = "+" + "-" * 64 + "+"
    output_func("\n".join([border] + ["| " + _pad(row, 62) + " |"
                         for row in _wrap_lines(lines, 62)] + [border]))


def roster_text(dice):
    return "  ".join(f"{i}[{die_label(die, symbols_enabled())}]" for i, die in enumerate(dice, 1))


def inspect_dice(state, command, output_func=print, other_dice=None):
    if command in ("h", "help"):
        show_panel(["DICE HELP", "L/♣: 1 and 6. T/♦: 2. O/▲: odd. E/■: even.",
                    "D/♠: Devil replaces 1. A/♥: Angel replaces 5.",
                    "M: Momentum scores earlier successes. R: Rescue, once per battle while available.",
                    "* is a wildcard face: combinations only, never a scoring single.",
                    "B/S/G: Bronze/Silver/Gold. Slots stay fixed this battle.",
                    "I 3: inspect active die. I other 3: inspect other roster.",
                    "Select available slots. R rolls; B banks; Q quits."], output_func)
        return True
    if not command.startswith("i "):
        return False
    try:
        parts = command.split()
        other = len(parts) == 3 and parts[1] == "other"
        if len(parts) != (3 if other else 2):
            raise ValueError
        slot = int(parts[-1])
        dice = (other_dice if other_dice is not None else getattr(state, "other_dice", None)) if other else state.dice
        if dice is None or not 1 <= slot <= 6:
            raise ValueError
        die = dice[slot - 1]
        odds = "  ".join(f"{'*' if face == 0 else face}:{100*p:.1f}%"
                         for face, p in face_distribution(die.kind, die.quality))
        description = [die_effect_text(die)]
        if die.kind in ("devil","angel"):
            description.append("Unique Silver: once per run, no upgrades or use charges.")
        show_panel([f"DIE {slot}: {die.kind} / {die.quality}", f"Item ID: {die.serial}", odds]+description, output_func)
    except (ValueError, IndexError):
        show_panel(["Use I 1..6, or I other 1..6."], output_func)
    return True


def render_gamebar(state, turn_number, roll, selected_positions, message, commands,
                   match_scores=None, active_side="Player", score_ambition=None,
                   first_turn="", ai_label="Easy", ai_details="", run_context=""):
    """Build one text frame without changing state or calculating rules.

    The battle controller supplies the available commands and result message.
    Display the latest roll even after the core clears its pending roll.
    """
    width = 62
    border = "+" + "-" * (width + 2) + "+"
    lines = [
        "THE KING'S GAMBIT - " + (f"PLAYER VS {ai_label.upper()} AI" if match_scores is not None
                                  else "SINGLE-PLAYER PRACTICE"),
        f"Turn: {turn_number}    Phase: {state.phase}",
        f"Banked score: {state.match_score} / {state.target}",
        f"Unbanked score (at risk): {state.unbanked_score}",
        f"Dice available next: {state.dice_available}",
        "",
    ]
    if run_context:
        lines.insert(1, run_context)
    if match_scores is not None:
        # Read the current side's live score; the match saves it at turn end.
        scores = dict(match_scores)
        scores[active_side] = state.match_score
        lines[2:2] = [
            f"Active side: {active_side}",
            f"Player: {scores['Player']}    Opponent: {scores['Opponent']}",
            ai_details or f"Easy AI score ambition: {score_ambition}",
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
    if state.dice is not None:
        scores = dict(match_scores or {})
        scores[active_side] = state.match_score
        lines = ["THE KING'S GAMBIT - " + ai_label.upper(), run_context,
                 f"Player: {scores.get('Player', 0)}  AI: {scores.get('Opponent', 0)}  Target: {state.target}",
                 f"Turn: {turn_number}  Side: {active_side}  Phase: {state.phase}", first_turn,
                 f"AT RISK: {state.unbanked_score}  Next roll: {state.dice_available}"]
        faces = dict(zip(state.roll_slots, roll)) if state.phase == "select" else {}
        tiles = []
        for slot in state.available_slots if state.is_active else []:
            face = faces.get(slot, "?")
            face = "*" if face == 0 else face
            tiles.append(f"{slot+1}[{face} {die_label(state.dice[slot], symbols_enabled())}]")
        lines += ["AVAILABLE: " + (" ".join(tiles) or "none"), "SET ASIDE: " + (" ".join(
            f"{slot+1}[{face} {die_label(state.dice[slot], symbols_enabled())}]"
            for slot, face in sorted(state.held_faces.items())) or "none")]
        other = getattr(state, "other_dice", None)
        if other:
            lines.append("OTHER: " + roster_text(other))
        if state.last_mapping:
            lines.append(f"Wildcard conversion: {state.last_mapping}")
        lines += [f"Result: {message}", f"Actions: {commands}", "H: help | I slot: inspect | Q: quit"]
        if ai_details:
            lines.insert(4, ai_details)
        if state.phase == "ended" and roll:
            lines.insert(6, "Last roll: " + str(["*" if n == 0 else n for n in roll]))
    # Stack two equal-width boxes so an ordinary 80-column terminal fits them.
    frame = []
    for panel in (rules, lines):
        frame.append(border)
        for row in _wrap_lines(panel, width):
            frame.append("| " + _pad(row, width) + " |")
        frame.append(border)
    return "\n".join(frame)


def show_gamebar(state, turn_number, roll, selected_positions, message,
                 commands, output_func=print, refresh=None, match_scores=None,
                 active_side="Player", score_ambition=None, first_turn="",
                 ai_label="Easy", ai_details="", run_context="", actions=None, selection_score=0,
                 dialogue="", action_fact=""):
    """Refresh an interactive terminal; keep captured output readable.

    Tests inject an output function, so they never clear the user's terminal.
    Native cls/clear needs no terminal library or cursor-timing assumptions.
    """
    if present(output_func, "battle", state=state, turn_number=turn_number,
               roll=roll, selected_positions=selected_positions, message=message,
               commands=commands, match_scores=match_scores, active_side=active_side,
               first_turn=first_turn, ai_label=ai_label, ai_details=ai_details,
               run_context=run_context, actions=actions or [], selection_score=selection_score,
               dialogue=dialogue, action_fact=action_fact):
        return
    if refresh is None:
        refresh = output_func is print and sys.stdout.isatty()
    if refresh:
        os.system("cls" if os.name == "nt" else "clear")
    output_func(render_gamebar(state, turn_number, roll, selected_positions,
                              message, commands, match_scores, active_side,
                              score_ambition, first_turn, ai_label, ai_details, run_context))


def show_run_summary(run, message, output_func=print):
    """Display supplied campaign state without deciding progression rules."""
    if present(output_func, "run_score" if run.score_summary is not None else "run_summary",
               run=run, message=message,story=run_story(run),score=run.score_summary):
        return
    if run.score_summary is not None:
        show_panel([run_story(run),message]+[
            f"{row['label']}: {row['value']} -> {row['points']} points" for row in run.score_summary["rows"]]+
            [f"TOTAL SCORE: {run.score_summary['total']} (formula v1)"],output_func)
        return
    width = 62
    border = "+" + "-" * (width + 2) + "+"
    lines = ["THE KING'S GAMBIT - RUN", f"Stage: {run.encounter_index + 1}/5",
             f"HP (extra lives): {run.hp}  Coins: {run.coins}", roster_text(run.dice), "", message]
    for result in run.history:
        scores = result["scores"]
        lines.append(f"Stage {result['stage']} {result['ai_type']}: {result['winner']} wins, "
                     f"Player {scores['Player']} / Opponent {scores['Opponent']}")
    if output_func is print and sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    rows = ["| " + _pad(row, width) + " |" for row in _wrap_lines(lines, width)]
    output_func("\n".join([border] + rows + [border]))
