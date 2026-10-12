# AGENTS.md

> Document version: 2.4
>
> Updated: 8 October 2026
>
> Status: One player-versus-Easy-AI match implemented with visible paced decisions; rewards and progression deferred.

## Confirmed decisions in this revision

- The 21 September design merge replaces the earlier scoring values: three 1s
  score 500; each matching die beyond three adds 200; straights score 500/600/1200.
- Ordinary three pairs are an explicit +0 six-die reroll, preserving earlier
  turn points; consecutive pairs have dedicated scores. See `docs/game_rules.md`.
- Current code and tests implement the revised base rules in single-player
  practice, including pair rerolls and a banked 2,000-point victory target.
- Single-player turn coordination now lives in `battle.py`; `ui.py` renders
  the refreshed ASCII gamebar and parses input (implemented 6 October 2026).
- The 7 October user request authorizes one simple Easy AI opponent match.
  Decisions are visible in the gamebar; rewards, shops, HP and five encounters
  remain outside this implementation stage. Practice remains available.
- The current opponent defaults to score ambition 500 (a starting value,
  not final five-opponent balance), with a 2-second pause per action.
  CLI options `--ambition` and `--ai-delay` adjust these values.
- Each opponent match starts with one fair 0/1 roll: 0 means AI first,
  1 means Player first. Show the result in the gamebar; practice stays Player-only.
- CLI opponent matches write local UTF-8 `.txt` event records in `match_logs/`,
  named by the local start timestamp. Record dice, selections, AI reasons and
  banked/unbanked scores; flush each event. Practice and direct core calls do
  not create personal logs. File handling lives in `main.py`, not the UI/scorer.
- V1 uses the reference's Easy AI; Normal/Hard and stochastic action sampling
  are not authorized V1 implementation requirements.

- Hot dice are active in Version 1. After all six dice score, all six become
  available to roll again while the accumulated turn score remains at risk.
- Each opponent banks when its unbanked score reaches or exceeds its configured
  score ambition.
- An opponent always banks immediately when doing so would win the match.
- Reward/relic stacking and post-loss encounter resets remain deferred until
  the basic version is being built.

## Project mission

Build Version 1 of *The King's Gambit*, a short medieval dice roguelite whose
central decision is whether to bank the current turn score or roll again and
risk losing it.

Every gameplay feature must strengthen that decision. Do not expand the game
beyond the Version 1 scope to add unrelated systems or presentation.

## Sources of truth

Use the project documents in this order:

1. The user's current instructions.
2. `docs/game_rules.md` for exact dice, scoring, banking, bust, hot-dice, and
   AI banking rules.
3. `docs/game_design.md` for product scope, run structure, architecture, UI,
   progression, and completion criteria.
4. `TODO.md` for unresolved decisions and implementation work.

If two documents conflict, follow the higher-priority source and update the
lower-priority document when the task authorizes documentation changes. Do not
silently choose a new rule.

## Version 1 scope

Implement:

- a fully playable Python command-line game using the standard library;
- one continuously refreshed ASCII gamebar;
- a fixed run of five encounters: normal, normal, elite, strong, and boss;
- 3 player HP, with 1 HP lost for a defeated encounter;
- alternating player and opponent dice turns;
- a default match target of 2,000 points;
- rewards after designated encounters, one simple shop, gold, healing, relics,
  and a small set of special dice;
- victory after defeating the boss and defeat when HP reaches 0; and
- clear instructions, input validation, and automated tests.

Do not add:

- a branching map, movement, or exploration;
- networking or multiplayer;
- permanent progression between runs;
- a large inventory or large content set;
- complex animation or audio systems;
- machine-learning AI; or
- required third-party dependencies.

PyGame may be used only with tutor approval. If it is approved, keep all game
rules independent from the display layer and retain a testable core.

## Core game rules

- Roll 0/1 once before the first turn of each opponent match to choose the
  starting side (0 = AI, 1 = Player). It is not a scoring die.
- A turn starts by rolling six dice.
- A successful roll requires the player to select at least one valid scoring
  die or complete combination from that roll, or explicitly activate ordinary
  three pairs for a +0 six-die reroll.
- Selected points are added to the unbanked turn score.
- Banking transfers all unbanked points to the match score and ends the turn.
- A roll with no positive scoring choice and no ordinary three-pair action is
  a bust: the entire unbanked turn score is lost, the match score is unchanged,
  and the turn ends.
- Combinations must be formed within one roll; never combine dice from separate
  rolls.
- Unbanked points cannot win a match. A side reaches the target only by banking.
- Hot dice are active. When all six dice have scored during a turn, make all six
  dice available again and allow the side to bank or continue rolling with the
  accumulated turn score still at risk.

The initial scoring validator must support:

| Selection | Score |
|---|---:|
| Single 1 | 100 |
| Single 5 | 50 |
| Three 1s | 500 |
| Three 2s | 200 |
| Three 3s | 300 |
| Three 4s | 400 |
| Three 5s | 500 |
| Three 6s | 600 |

After this validator is reliable and tested, enable the four-to-six-of-a-kind
and straight rules, then ordinary three pairs and consecutive pairs, as
documented in `docs/game_rules.md`. Never use zero points alone to mean an
invalid action: ordinary three pairs are legal and immediately reroll six dice.

## AI rules

Each opponent has a score ambition, meaning the unbanked score at which it
banks.

- Select the legal action with the highest immediate score; resolve ties with
  the lexicographically earliest ascending position tuple. If only
  ordinary three pairs are legal, activate their reroll.
- Bank when the unbanked turn score reaches or exceeds the configured score
  ambition.
- Continue rolling while below the score ambition.
- Bank immediately if banking would reach or exceed the match target, even when
  below the normal score ambition.
- Use the same scoring, bust, selection, and hot-dice rules as the player unless
  an explicitly documented opponent ability modifies them.
- Keep decisions deterministic and explainable. Randomness should come from
  dice rolls, not hidden AI choices.

## Architecture

Target this module structure:

```text
the_kings_gambit/
|-- main.py
|-- dice.py
|-- scoring.py
|-- models.py
|-- battle.py
|-- progression.py
`-- ui.py
tests/
|-- test_dice.py
`-- test_scoring.py
```

Maintain these boundaries:

- `main.py` starts the application and contains no scoring logic.
- `dice.py` rolls dice and supports injected randomness for deterministic
  tests.
- `scoring.py` validates selections and calculates points. It performs no
  input/output.
- `models.py` owns player, opponent, match, and run state without controlling
  the UI.
- `battle.py` coordinates turns and AI decisions through the smaller modules.
- `progression.py` controls encounters, rewards, shops, HP, and run outcomes;
  it performs no individual dice calculations.
- `ui.py` renders state and collects validated commands; it contains no game
  rules.

Prefer explicit state transitions and small, pure functions for scoring and
validation. Do not duplicate rule calculations in the UI or AI.

## Unresolved rules

Reward/relic stacking order and the exact reset flow after an encounter loss
will be decided while the basic version is being built. Until they are decided:

- keep effect application and encounter-reset logic isolated;
- use clear function names and minimal interfaces so behaviour can be changed;
- do not present a temporary assumption as a final design decision; and
- record any necessary temporary behaviour in `TODO.md` and tests.

Do not allow these deferred decisions to block independent work on dice,
scoring, selection validation, models, or a single basic match.

## Development order

Work in this sequence unless the current task explicitly requires otherwise:

1. Dice rolling.
2. Scoring and selection validation.
3. Player and opponent state.
4. ASCII display and input validation.
5. One complete player-versus-AI match.
6. Rewards, shop, and five-encounter progression.
7. Menus, victory/defeat screens, balancing, and final documentation.

Keep changes small and focused. When behaviour changes, update the relevant
rule document and tests in the same change.

## Testing requirements

Use the standard-library `unittest` framework unless the project deliberately
adopts another test runner.

Test at minimum:

- every revised scoring combination and invalid selection;
- ordinary three-pair +0 rerolls, preserved turn score, repeated activation,
  optional positive subsets, and consecutive-pair priority;
- combinations being rejected across separate rolls;
- banking and bust state transitions;
- both opening-roll outcomes, one opening roll per match, and unchanged practice;
- hot dice returning all six dice while preserving the unbanked score;
- the AI banking at its score ambition;
- the AI banking when it can win;
- match records for decisions, score changes, victory and quitting; logging tests
  use temporary directories and must not populate the user's `match_logs/`;
- match victory, encounter loss, HP reaching zero, and boss victory;
- reward, shop, gold, healing, and relic effects once implemented; and
- malformed input without application crashes.

Use seeded or injected randomness in tests. Tests must not depend on lucky
rolls, terminal timing, or manual input.

Run the full test suite before declaring a task complete. Once the package and
tests exist, the expected standard-library command is:

```powershell
python -m unittest discover -s tests
```

If the actual entry point or test command changes, update this file and the
README.

`python main.py` starts one player-versus-Easy-AI match. Use
`python main.py --practice` for the original single-player mode.

## Completion standard

A change is complete when it:

- follows `docs/game_rules.md` and the Version 1 scope;
- preserves module boundaries;
- handles invalid input and edge cases without crashing;
- adds or updates proportionate automated tests;
- leaves the game runnable; and
- updates affected documentation and open decisions.

Version 1 is complete only when a player can finish the five-encounter run, all
core state changes are reflected in the gamebar, the AI completes turns
automatically, HP and progression work correctly, the boss can be defeated,
zero HP ends the run, and victory and defeat summaries are displayed.
