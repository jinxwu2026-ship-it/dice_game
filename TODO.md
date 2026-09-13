# Project To-Do

This file records design decisions and implementation questions that must be
resolved for Version 1 of *The King's Gambit*.

## Game rules

- [x] Define the base dice-scoring values and turn flow.
  See [`docs/game_rules.md`](docs/game_rules.md).
- [x] Confirm whether using all six dice for scoring activates "hot dice" and
  allows the player to roll all six dice again. Hot dice are enabled.
- [x] Confirm that the 2,000-point match target can only be reached by banking
  the current turn score. Section 2 of `game_rules.md` states that unbanked
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

- [x] Add project-specific instructions to `AGENTS.md`.
- [ ] Add exact commands for running the game and automated tests once the
  initial project structure exists.
- [ ] Keep the ASCII UI, input handling, scoring rules, battle flow, and run
  progression in separate modules as described in `docs/game_design.md`.
- [ ] Add tests for scoring, selection validation, banking, busts, invalid
  input, and important state transitions.
