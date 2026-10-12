# Project To-Do

This file records design decisions and implementation questions that must be
resolved for Version 1 of *The King's Gambit*.

## 21 September design merge / 新规则迁移

- [x] Merge the supplied scoring and AI document into the design and rules;
  archive its original text in `docs/scoring_and_ai_reference.md`.
- [x] Specify 111 = 500, +200 per matching die beyond three, and straights
  500/600/1200; define ordinary and consecutive three-pair actions.
- [x] Retain fixed score-ambition banking for V1; keep Normal/Hard as research.
- [x] Migrate scoring constants and expected test values: 111 = 500,
  matching dice beyond three add 200, straights 500/600/1200.
- [x] Introduce legal action metadata; distinguish invalid selection from a
  legal +0 ordinary three-pair action. Update `calculate_score`,
  `score_selection`, legal-action enumeration, and `is_bust` together.
- [x] Implement ordinary three-pair immediate rerolls, prior score preservation,
  repeated activation and optional 1/5 subsets; implement consecutive pairs
  and their precedence. Use the test matrix in `docs/game_rules.md` section 6.
- [x] Update turn state and UI instructions for the revised rules; prevent
  banking before selecting or between ordinary three-pair activation and reroll.
- [x] End single-player practice when banking reaches or exceeds 2,000;
  test exact-target and overshoot victories, malformed input, EOF and Ctrl-C.
- [x] Implement one shared-action Easy AI with highest immediate scoring selection;
  document and test lexicographically earliest positional tie-breaking.
- [x] Test ambition banking, winning-bank priority, alternating turns and both
  match outcomes; show and pace AI rolls, selections and decisions.
- [ ] Configure and balance five ambitions. The single opponent's 500-point
  default is a starting value for manual testing, not final encounter balance.
- [ ] Implement and test five-encounter run progression.
- [ ] Reproduce probability and strategy claims before using them for balance:
  record rule version, action phases, seed, sample count, error and solver convergence.
- [ ] Evaluate Normal/Hard only after the basic version, with an explicit scope
  decision; their dynamic thresholds must not silently replace V1 ambition.

## Game rules

- [x] Roll 0/1 once at the start of each opponent match (0 = AI, 1 = Player);
  display the result and test both starts, subsequent turns and unchanged practice.
- [x] Define the base dice-scoring values and turn flow.
  See [`docs/game_rules.md`](docs/game_rules.md).
- [x] Confirm whether using all six dice for scoring activates "hot dice" and
  allows the player to roll all six dice again. Hot dice are enabled.
- [x] Confirm that the 2,000-point match target can only be reached by banking
  the current turn score. Section 4 of `game_rules.md` states that unbanked
  points do not become part of the match score until they are banked.
- [x] Define the AI's banking behaviour. The AI banks when its unbanked turn
  score reaches or exceeds its configured score ambition. It always banks when
  doing so would win the match.
- [ ] Define how reward and relic effects stack, including their order of
  operation. Decide this while building the basic version; do not invent a
  final stacking model before the underlying systems exist.
- [ ] Define the flow after an encounter loss, including which state resets
  before the next encounter. Decide this while building the basic version.

## Project guidance

- [x] Save only CLI opponent matches as timestamped UTF-8 text in `match_logs/`;
  record dice, decisions/reasons, banked/unbanked scores and outcomes. Flush
  events, preserve prior files and keep automated tests out of personal logs.
- [x] Add project-specific instructions to `AGENTS.md`.
- [x] Document `python main.py` for an opponent match, `--practice` for solo
  practice, AI ambition/delay options and the automated test command.
- [x] Move single-player turn orchestration from UI to `battle.py`.
- [x] Add a refreshed single-player ASCII gamebar with turn/phase, scores,
  target, dice, selected positions, available dice, commands and result messages.
- [x] Test gamebar state transitions, wrapping, refresh behavior and exit handling.
- [x] Place scoring help in a separate equal-width box above the gamebar;
  replace the side-by-side layout to fit standard 80-column terminals.
- [ ] Keep the ASCII UI, input handling, scoring rules, battle flow, and run
  progression in separate modules as described in `docs/game_design.md`.
- [x] Add tests for the revised dice-rule core: scoring, selection validation,
  banking, busts, malformed values, and hot-dice state transitions.
