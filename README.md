# The King's Gambit

**English** | [简体中文](README.zh-CN.md)

Roll for more points, or bank before you lose them. Play the full five-battle
dice roguelite in a window or in the terminal.

## Quick start

Install **Python 3.10 or newer** (tested with Python 3.12.10). Download or clone
this repository, then open a terminal in the project folder containing `main.py`
and `requirements-gui.txt`. The commands below create a local environment and
install the window version's only external dependency, **pygame-ce 2.5.8**.
You do not need to activate the environment.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-gui.txt
.\.venv\Scripts\python.exe main.py --gui
```

If the environment is already installed, run only the last command. If Windows
does not recognize `python`, use `py` for the first command.

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-gui.txt
./.venv/bin/python main.py --gui
```

These are the standard platform-specific environment commands; macOS/Linux
desktop operation has not yet been verified. On Linux, `venv` must be available
in your Python installation.

### Start playing

Choose **New Run** from the window's main menu. Draw or skip the opening gifts,
then choose your wager; a zero-coin wager is allowed. In battle:

1. Click dice to move them into the selection tray; click again to undo.
2. Choose **Confirm +N** to commit a legal scoring selection.
3. Choose **Bank** to keep the turn's points, or **Roll** to risk them for more.
   Bust loses the unbanked points; Bank and Bust advance automatically.

Open **Rules** from the menu or during play for illustrated scoring examples.
The interface is in English in both README language versions.

### Terminal version (no external packages)

No pygame installation is needed for these commands. On Windows use `python`;
on macOS/Linux use `python3` instead.

```powershell
python main.py --run       # Complete five-battle run
python main.py --help     # All command-line options
```

Enter dice positions such as `1 3 5`, then `R` to roll or `B` to bank. In the CLI,
press Enter after completed turns; `Q` quits. `--ascii` replaces special symbols
with letters. `--ai-delay 0` removes the default two-second AI reading pauses.

GUI and CLI runs save local `.txt` records in `match_logs/`.
There is no save/resume for an unfinished run.

For a course submission, the graphical version must be run on a local computer
with a desktop display; it is not supported in the Ed execution environment.
Include `main.py`, the whole `the_kings_gambit/` package, `assets/`, and
`requirements-gui.txt` when sharing the window version. Do not include `.venv/`
or personal `match_logs/` files.

Only runtime code, required artwork, the two READMEs and dependency files are
published. Design notes, screenshots, tests, analysis tools, local environments
and personal logs stay in the development workspace. References marked **local**
below refer to that workspace, not files included in the public repository.

## About the game

*The King's Gambit* is a short medieval dice roguelite inspired by the Dice
minigame in *Kingdom Come: Deliverance II*. The player faces five gamblers in a
fixed sequence and must decide when to keep rolling for a higher score and when
to bank points safely.

The game has a standard-library command-line interface and an optional
pygame-ce mouse interface. Both use the same rule and progression controllers.

## Window interface

The English main menu offers **New Run**, **Leaderboard**, **Rules**, **Quit**.
It follows the minimal V3 concept: thin separators, 52-pixel dice, HP/coins
bottom-left, both score bars top-left, opponent emblem top-center, turn score
top-right. Only the active side's dice are shown. Click available dice to move
them to the left tray; click them again to return them. **Confirm +N** commits
the preview; **Clear selection** returns the unconfirmed dice. Only after
confirmation do **Roll N**/**Bank S** appear, with the risk and resulting banked
total. Ordinary three pairs instead offer **Reroll Six (+0)**. Hover or focus a
die for its effect and actual face probabilities. Disabled actions cannot submit.

Use **Tab / Shift+Tab** or arrow keys to move focus, **Enter / Space** to activate,
and **1–6** to toggle selectable fixed dice slots. Focus has corner marks;
selected dice have check marks. All growth screens also support keyboard focus.

**Rules** is also available at the top-right during play. Its two illustrated pages
show real dice faces for singles, triples, extra matches, straights and pairs.
For example, three 3s show 300, then one extra 3 shows +200. Scores come from the
shared scorer. Closing the overlay preserves your pending selection; automatic
turn changes wait while it is open, while AI actions continue in the background.
Escape closes the top overlay; window-close confirmation appears above Rules.
Matching-dice reference (local: `docs/ui_concepts/pygame_ce_rules_matches_2026-10-30.png`) ·
Straight/pair reference (local: `docs/ui_concepts/pygame_ce_rules_combinations_2026-10-30.png`).

Special dice use family colours with inset type marks. Bronze,
Silver and Gold have thick metal rims, quality bands, B/S/G and one to three
notches. Devil/Angel wildcard faces have their own heads; their rules are unchanged.
Each roll has a short turning/bouncing animation; **Skip animation** reveals the
same result immediately. Only available dice move, and gameplay input unlocks
after the animation. Playing or skipping consumes exactly the same game randomness.

**New Run** opens on the illustrated dragon's wager and the original initial
draw choices. Drawing offers three distinct Bronze kinds from Lucky/Two/Odd/Even/
Momentum. There is a **20%** chance to replace one random gift with **Silver Rescue**;
otherwise all three are Bronze. Keep or decline each gift separately; there is no
random empty draw or Lucky Silver branch. Ordinary dice remain in the game.
Current three-die opening (local: `docs/ui_concepts/pygame_ce_initial_three_dice_2026-10-30.png`).
**WARD** is the story name for existing extra lives: zero still
allows play, and losing to the Boss ends the run regardless of remaining wards.
The opening PNG is bundled at `assets/gui/dragon_wager_intro.png`; its generation
prompt and artwork notes stay in the local development workspace.

Wagers, rewards, merging, guessing, spinner and shop are mouse-driven. Choose
one reward destination before keeping it; **Preview Merge** does not consume
materials until placement is confirmed. **Merge Dice** at wager/shop merges
two matching equipped items without consuming the paid shop service.
**Bust** and **Bank** display the result for one second and continue automatically,
for both sides in every battle. Neither needs **Next Turn**. The exit confirmation
suspends automatic continuation. Hot Dice keeps all six completed dice in the left
tray until the next roll; only then do they return to the center. Basic-mode clicks
and equipped-mode clicks both take the exact physical dice shown in the preview.
Opponents now speak short lines alongside actual actions; full strategy reasons
remain in the `.txt` log. Events and all five opponents have brief story text.

Guess Size animates the actual die before showing a win/miss. The weighted
spinner slows down onto the already chosen sector. Both support **Skip animation**;
results stay visible until **Continue**, with no change to event odds.
Boss victory offers at least one **Gold** die: cash and lower-tier stakes also
qualify. A won Gold stake already fulfills this bounty, so it is not duplicated.
Matching-quality wager settlement and the enemy's battle equipment stay unchanged.

After rewards, the ending and seven-part **TOTAL SCORE** share one page. Formula v1
uses final wards ×500, earned income, accepted Bronze/Silver/Gold ×100/250/600,
best banked turn ÷5 (rounded down), +50 per extra successful roll in the longest
banked chain, +1000 for banking the entire target in one turn, and
`max(0, 500 × won battles − 20 × total turns)` for efficiency. Total turns count
both sides.
Income excludes the initial 100 coins, returned stakes and refunds. Bust losses
do not qualify as banked records. The existing UTF-8 run log saves the breakdown,
total and structured scoring history so the same calculation can be replayed.
These performance weights are provisional; encounter difficulty has not changed.

**Leaderboard** reads finished formula-v1 run scores from local `match_logs/*.txt`,
with eight rows per page. Victory and defeat runs are ranked by score, then newest
start for ties. Quits, unfinished/damaged files and older logs without scores are
excluded. Opening the page reloads history; it never edits logs or writes a second index.
Current leaderboard rendering (local: `docs/ui_concepts/pygame_ce_local_leaderboard_2026-10-30.png`).

Two new fair-faced dice can appear in run rewards, enemy equipment and shops:

- **Momentum** (purple / M): when legally scored, adds 100 per earlier successful
  scoring roll this turn, up to 400 per selection. Several selected Momentum dice
  share one bonus. Hot Dice restores the effect and keeps the count; Bank/Bust
  resets it. These are temporary playable values, with no balance claim.
- **Rescue** (grey-blue / R): while still available, optionally reroll the entire
  remaining pool once per battle. A failed roll offers **Use rescue** or **Accept
  Bust** before clearing points. At most one equipped; new battles refresh it.
  Fixed **Silver** in all sources; cannot merge or upgrade. Not globally unique.
  CLI: use `R` before confirming a selection or at the rescue prompt; `S` accepts Bust.

Momentum currently has identical effects at Bronze/Silver/Gold. Combination-specific
bonuses and one-use burst dice are still deferred.

AI actions are shown at the existing two-second pace. For quick testing:

```powershell
.\.venv\Scripts\python.exe main.py --gui --ai-delay 0
```

**Exit run**, Escape or closing the window opens a confirmation. **Keep playing**
is the default; Escape dismisses it. AI turns continue behind the dialog.
**End run** waits for wager refunds and log closure before returning to the menu
or closing the window. This version has no save/resume.
Actual window runs use the same timestamped UTF-8 logs
as CLI runs; automated experiments create no personal logs.
Window resizing preserves proportions, remaps mouse coordinates and keeps at
least 960×600; extra width is letterboxed.

Actual rendered V3 main menu (local: `docs/ui_concepts/pygame_ce_v3_menu_implemented.png`),
battle (local: `docs/ui_concepts/pygame_ce_v3_battle_implemented.png`),
Roll/Bank (local: `docs/ui_concepts/pygame_ce_v3_decision_implemented.png`) and
exit confirmation (local: `docs/ui_concepts/pygame_ce_v3_exit_implemented.png`) screenshots are saved
for comparison. Desktop click inspection was limited by the locked desktop;
automated mouse and keyboard tests cover the complete growth run, confirmed
cancellation and clicks at 960×600, 1280×800, 1600×900, 1920×1080 and 2560×1080.

Latest rendered opening (local: `docs/ui_concepts/pygame_ce_opening_2026-10-29.png`),
battle dice (local: `docs/ui_concepts/pygame_ce_dice_2026-10-29.png`) and
dice catalogue (local: `docs/ui_concepts/pygame_ce_dice_catalog_2026-10-29.png`) show the
29 October artwork and skin update. Latest examples show
automatic Bust (local: `docs/ui_concepts/pygame_ce_bust_auto_2026-10-29.png`),
AI dialogue (local: `docs/ui_concepts/pygame_ce_ai_dialogue_2026-10-29.png`),
Rescue (local: `docs/ui_concepts/pygame_ce_rescue_2026-10-29.png`) and
Momentum previews (local: `docs/ui_concepts/pygame_ce_momentum_2026-10-29.png`).

Current menu (local: `docs/ui_concepts/pygame_ce_menu_2026-10-29.png`),
guess result (local: `docs/ui_concepts/pygame_ce_guess_result_2026-10-29.png`),
spinner result (local: `docs/ui_concepts/pygame_ce_spinner_result_2026-10-29.png`) and
run score (local: `docs/ui_concepts/pygame_ce_run_score_2026-10-29.png`) renderings.

## Project status

The dice-rule core and fixed five-stage Player-versus-AI run are implemented and
tested. GUI and CLI share scoring, selection validation, busts, banking, Hot Dice
and progression. The run includes one extra life, wagers, victory money, events,
rewards and a shop.

A headless AI-versus-AI simulator is also available. Normal's conservative,
neutral, aggressive and composite personalities work in both CLI and simulation;
Hard is paused. Easy is the first-stage opponent.

The revised scoring rules are implemented:
three 1s = 500, matching dice beyond three add 200, and straights = 500/600/1,200.
Ordinary and consecutive three pairs, repeated hot dice, and legal zero-point
actions are supported. Each battle alternates player and AI turns and ends when
either side banks at least 2,000 points. Campaign stages use fresh scores;
equipment and coins carry between stages; see TODO.md (local: `TODO.md`) for remaining balance work.

The growth/event rules are playable using `--run`:
game_rules section 8 (local: `docs/game_rules.md#8-已确认的成长与事件规则`),
游戏流程 (local: `docs/游戏流程.md`), 骰子规则 (local: `docs/骰子规则.md`).
The adopted event order is guessing after stage 1, spinner after stage 3, then the shop after stage 4.
骰子效果设计分析 (local: `docs/骰子效果设计分析.md`) records the implemented six-die subset
and remaining effect/set candidates. Relics and set bonuses are not implemented.
Earlier 经济实验 (local: `docs/数值与事件分析.md`) and `python tools/economy_analysis.py`
reproduce a historical five-item-spinner, unrestricted-tier model, not these latest rules.
They do not simulate special-dice combat or measure actual AI strength.

The CLI gamebar shows the turn number, phase, banked score and target,
unbanked points, latest dice, selected positions, available dice, commands and
result messages. It refreshes in place in an interactive terminal; redirected
output and automated tests retain readable frames instead of clearing the screen.
Scoring rules appear in a separate box at the top, immediately followed by
the gamebar. Both boxes are 66 columns wide and fit a standard 80-column
terminal without the wrapping caused by the earlier side-by-side layout.

## Basic game rules

- Before each opponent match, one fair 0/1 roll chooses who starts:
  0 = AI, 1 = Player. The gamebar keeps the result visible. It is not a scoring
  die and is not repeated between turns.
- The player and opponent take alternating turns.
- A turn begins by rolling six dice.
- The player selects a valid scoring subset, or explicitly activates an ordinary
  three-pair +0 six-die reroll while preserving earlier turn points.
- Selected points are added to the unbanked turn score.
- The player may bank the score and end the turn, or roll the remaining dice
  and risk the unbanked points.
- A roll with neither a positive scoring choice nor an ordinary three-pair
  action is a bust. All unbanked points from that turn are lost.
- Banked points are safe. The first side to bank enough points to reach the
  match target wins the encounter.
- The default Version 1 match target is 2,000 points.
- Hot dice are enabled: after all six dice score, all six become available to
  roll again while the accumulated turn score remains at risk.

### Basic scoring

| Dice or combination | Points |
|---|---:|
| Single 1 | 100 |
| Single 5 | 50 |
| Three 1s | 500 |
| Three 2s | 200 |
| Three 3s | 300 |
| Three 4s | 400 |
| Three 5s | 500 |
| Three 6s | 600 |

The revised full rules add 200 per matching die beyond three; straights score
500/600/1,200. Ordinary three pairs allow +0 rerolls; consecutive pairs
112233/223344/334455/445566 score 1,200/1,000/1,100/1,200 and activate hot dice.
Two triples add their values with no extra bonus. See
docs/game_rules.md (local: `docs/game_rules.md`) for the complete scoring table,
selection rules, and examples.

## Run structure

Use `python main.py --run` for the following fixed encounters:

1. Common enemy: Easy (ambition 500, pending balance).
2. Common enemy: Normal conservative.
3. Common enemy: Normal aggressive.
4. Elite enemy: Normal neutral.
5. Boss: Normal composite, not Hard.

The run starts with 100 coins and six basic dice. An optional initial draw precedes
Easy; guessing follows stage 1, the six-item spinner follows stage 3, and the shop
follows stage 4. Victory bonuses are 200/200/250/350/500, with none on losses.
Enemy personalities stay fixed; their equipped special dice are generated per stage.

HP counts extra lives, starting at 1. For the first four stages, a loss at HP=1
consumes it and advances to the next stage with HP=0, not a retry. HP=0 is still
playable; a further loss ends the run. Losing to the Boss always ends the run,
even with an extra life. Defeating the Boss wins. Each stage starts with both
scores at zero, fresh turn state and a new opening 0/1 roll; HP, coins and the
player's equipment carry over. Enter advances after a stage; Q/EOF/Ctrl-C quits
without another life loss. An unfinished cash wager is refunded on quitting.

### Play the growth version

```powershell
python main.py --run
python main.py --run --ai-delay 0
python main.py --run --ascii
```

The default pauses two seconds per AI action. Use `--ascii` if the terminal's
font displays suit symbols badly; unsupported output encodings fall back automatically.

| Screen | Commands |
|---|---|
| Initial draw | Enter/P draws, S skips |
| Wager | `C 50` bets cash; Enter bets 0; `D 2` stakes your slot 2 at an actual matching quality |
| Select dice | Type available fixed slots, e.g. `1 3 5` |
| After selection | R rolls, B banks |
| Inspect | H help; `I 3` active slot; `I other 3` other roster |
| Receive die | `1..6` replaces slot; `M 2` previews merging with slot 2; D declines/cancels |
| Equipped merge | `M 1 2` at wager/shop merges matching items free, result in slot 2 |
| Guess event | Enter/P joins; S small, B big; after a win B claims or R risks pending prizes |
| Spinner | Enter/P spins, S stops; up to three draws without replacement |
| Shop | `buy 2`, `upgrade 3`, `remove 3`, `refresh`, Enter/leave |

Q quits. Only a newly won battle die may be declined for 80% of its original
price; initial/event dice give no cash. Preview cancellation preserves materials.
The shop has one paid upgrade/removal service and one refresh; free merges do not consume the service.

| Die | Symbol / ASCII | Effect |
|---|---|---|
| Lucky | ♣ / L | Bias 1 and 6 |
| Two | ♦ / T | Bias 2 |
| Odd | ▲ / O | Bias 1, 3, 5 |
| Even | ■ / E | Bias 2, 4, 6 |
| Devil | ♠ / D | Replace natural 1 with wildcard `*` |
| Angel | ♥ / A | Replace natural 5 with wildcard `*` |

B/S/G marks quality. Biased faces have weight 2/3/4 by quality; other faces have
weight 1. Devil and Angel are always Silver, cannot upgrade, and each can be
generated only once per run across every source, including AI and unbought shop stock.
There are no use charges. Wildcards complete matching groups of 3–6 or straights
of 5–6; they cannot score singly or synthesize three pairs. The selected subset
uses its highest legal substitution, shown in the gamebar and log.
See dice rules (local: `docs/骰子规则.md`) for exact item handling.

## Opponents

Each Easy opponent has a score ambition that controls its risk level. The opponent
continues rolling while below this amount and banks once its unbanked score
reaches or exceeds it, except after **Hot Dice**: roll all six again before checking
the threshold at the next non-Hot scoring decision. Each new Hot Dice repeats this
rule. Banking an immediate win still takes priority. CLI, GUI and headless matches
share this Easy decision; Normal personalities are unchanged.

Easy AI uses the highest immediate scoring legal action. Equal-score choices
use the lexicographically earliest ascending position list. The default
score ambition is 500, a starting value for testing rather than final balance.
Its rolls, selected positions, score gains, Hot Dice and Bank/Roll reasons are
shown in sequence. Each action pauses for 2 seconds; Enter advances between
completed turns. Ctrl-C exits during AI playback without banking risked points.
Normal's turn-utility strategy is implemented; Hard's win-probability model remains paused.
For special equipment, Normal uses exact weighted probabilities with one future
positive-roll lookahead, replanning at each decision. The basic-dice full-turn
table remains unchanged. Earlier basic-dice win-rate reports do not establish
special-dice strength; this version is not a win-probability solver.
The AI is intended to be deterministic and easy to understand. It does not use
machine learning.

## Implemented and deferred features

- A continuously updated ASCII gamebar and optional mouse interface are implemented.
- Five opponents with different risk levels are implemented.
- Relics, additional effects and set bonuses remain design candidates.
- Gold, special dice, one shop and victory/defeat summaries are implemented.
- Healing is not included in the adopted shop rules.
- Invalid player input is validated.
- Automated tests cover scoring and game-state changes.

Version 1 does not include multiplayer, map exploration, permanent progression,
or a large inventory system.

## Requirements

- Python 3.10 or newer is recommended.
- The command-line version and headless simulation use only the standard library.
- The optional window interface requires `pygame-ce==2.5.8`, listed in
  [requirements-gui.txt](requirements-gui.txt).

## CLI run options

Play the complete five-stage sequence (one extra life):

```powershell
python main.py --run
```

To remove AI reading pauses or use letter labels:

```powershell
python main.py --run --ai-delay 0
python main.py --run --ascii
```

Normal compares expected turn utility, including remaining dice, rather than
using the Easy ambition. Gamma is 0.5/1/2 for conservative/neutral/aggressive.
Composite chooses a personality at the start of each AI turn using score gap
and opponent threat, and keeps it for that turn. Normal reasons and utilities
are shown and logged; utilities are not win probabilities. `--ambition` affects
only Easy (a supplied value must still be positive); `--ai-delay` applies to both.
Stage personalities are fixed and cannot be overridden for a run.

`--ai-delay 0` removes timed pauses; completed turns still wait for Enter.
The delay must be finite and non-negative; ambition must be a positive integer.

Enter positions such as `1 3 5` to select dice, then `R` to roll or `B` to bank.
After a completed turn, press Enter to start the next turn or Q to quit.
For ordinary three pairs, selecting all six positions explicitly activates a
zero-point reroll; there is no Bank prompt before that reroll. Selecting only
scoring 1s/5s instead remains possible. `Q`, EOF, or Ctrl-C exits the run.

`models.MatchState` tracks both scores, the active side and winner. `ui.py` only renders
frames and parses input; scoring and state changes stay in the core modules.
`progression.run_campaign()` coordinates stages and applies the confirmed extra-life
rules to `models.RunState`, reusing `battle.run_match()` for every stage.

## Match records

An actual GUI or CLI run is automatically saved as a UTF-8 text file
in `match_logs/`, named by the local start time, for example
`2026-10-08_15-30-20_123456.txt`. Microseconds distinguish starts within one
second; existing records are never overwritten. The CLI prints the saved path
when the run ends or you quit.

Each event records the turn number, acting side, dice in positional order,
selected positions, available dice, phase, both banked scores, the acting
side's current banked score and unbanked turn score. AI Bank/Roll reasons,
Hot Dice, ordinary three pairs, Bust losses and the winner or early exit are
included. Events are flushed immediately, so earlier actions survive an
interruption. On quit, any displayed unbanked points are discarded, not banked.

A whole campaign uses one
timestamped file containing RUN/STAGE start/end events and per-action stage/HP
context. It records final results and quitting; scores never carry across stages.
Direct controller calls without a writer (including automated tests/simulations)
do not create personal records.
Logging tests use temporary directories, not `match_logs/`. Records remain
local and are ignored by Git; there is no upload or automatic deletion.

## Headless AI experiments

Run the default 100-match Easy 500 versus Easy 500 experiment:

```powershell
python -m the_kings_gambit.simulation --games 100 --seed 20261013
```

Compare different Easy thresholds, for example:

```powershell
python -m the_kings_gambit.simulation --games 100 --ambition-a 500 --ambition-b 750 --seed 20261013
```

Select either side's Normal personality using `--ai-a` / `--ai-b`:

```powershell
python -m the_kings_gambit.simulation --games 100 --ai-a composite --ai-b easy --seed 20261013
python -m the_kings_gambit.simulation --games 100 --ai-a conservative --ai-b aggressive --seed 20261013
```

Default target is 2,000; `--target` can change it for experiments. Games, ambitions
and target must be positive integers; seed is an integer. Each match starts with
zero scores and stops immediately after a winning Bank. A/B alternate first
turns (100 matches: 50 each; for odd counts A starts once more). Match index i
uses seed+i. This controlled start is for experiments only: gameplay retains
its random opening 0/1. Dice consumption changes with policies, so using the
same seed for different policies does not mean identical rolls for every turn.

Results include wins, approximate 95% Wilson intervals, first/second-turn wins,
turns, rolls, Bust rates, mean points per Bank (excluding Bust), Hot Dice,
ordinary pairs and batch runtime. Core experiment calls are reproducible except
for elapsed time. No UI, manual input, pauses or file writes occur; personal
`match_logs/` is never used. Safety limits abort explicitly, not as fake draws.

The 100-game experiment is separate from unittest and is a preliminary sample,
not proof that an ambition is optimal. See Normal implementation (local: `docs/normal_ai_design.md`)
and Normal's 100-game preliminary results (local: `docs/normal_ai_results.txt`).
The two 13 October Easy smoke experiments are saved in
baseline results (local: `docs/ai_simulation_baseline.txt`); these do not change the
game's default ambition of 500.

Run every pair among Easy 500 and the four Normal personalities:

```powershell
python -m the_kings_gambit.simulation --round-robin --games 1000 --seed 2026102600
```

Here `--games` means games per pair: five profiles produce ten pairs and 10,000
matches. Each pair gets a separate seed range starting at `seed + pair_index * games`;
round-robin requires an even count so both sides get equal starts. Its default
seed is 2026102600, separate from the pairwise default of 20261013.
Pair order follows `AI_TYPES` in `ai.py`.
Round-robin fixes Easy at 500 and rejects conflicting pairwise AI/ambition options.
It prints a win-rate matrix, descriptive pool rates and the usual pair reports,
without tuning parameters or writing files. These are measured matchup rates,
not Normal's decision-time utility values or a guarantee of increasing difficulty.
Large runs print the report after all pairs finish; this 10,000-match run took
about four minutes on the current environment, not a fixed runtime guarantee.
See 26 October cross-play results (local: `docs/ai_round_robin_2026-10-26.txt`).

## Running tests

The `tests/` folder stays local and is not included in the public runtime files.
The following commands apply to the full development workspace.

Run the automated tests with:

```powershell
python -m unittest discover -s tests
```

To include pygame rendering and mouse tests, run inside the GUI environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

On macOS/Linux:

```bash
./.venv/bin/python -m unittest discover -s tests
```

Without pygame-ce, the optional rendering tests skip while core and bridge
tests run. GUI tests use an offscreen SDL display, injected dice and temporary
logs; they never write into your personal `match_logs/`.

## Local development documentation

- Game design (local: `docs/game_design.md`) — concept, scope, run structure, UI, and
  completion criteria.
- Game rules (local: `docs/game_rules.md`) — exact scoring and turn rules.
- Scoring and AI reference (local: `docs/scoring_and_ai_reference.md`) — archived source;
  statistical claims await independent reproduction.
- Normal AI implementation (local: `docs/normal_ai_design.md`) — three fixed personalities
  and a situation-based composite; Hard paused.
- Hard AI memo (local: `docs/hard_ai_memo.md`) — brief offline win-model ideas only;
  not an implementation requirement or the current Boss strategy.
- Project to-do list (local: `TODO.md`) — unresolved decisions and development work.
- Agent guidance (local: `AGENTS.md`) — implementation boundaries and quality
  requirements.

## Full local project structure

```text
README.md                       # English guide
README.zh-CN.md                 # Simplified Chinese guide
requirements-gui.txt            # Optional pygame-ce dependency
main.py                         # CLI/window launcher
the_kings_gambit/
|-- main.py                      # CLI options and personal log files
|-- dice.py                      # Physical dice and weighted rolls
|-- scoring.py                   # Legal subsets and wildcard substitution
|-- models.py                    # Item, turn, match and run state
|-- battle.py                    # Shared player/AI turns
|-- ai.py                        # Normal utility and personalities
|-- simulation.py                # Headless basic-dice AI experiments
|-- progression.py               # Wagers, rewards, events, shop and five stages
|-- run_score.py                 # Replayable seven-part run score; no I/O
|-- gui_session.py               # Worker, immutable display snapshots and input requests
|-- gui.py                       # pygame-ce rendering and mouse interaction
`-- ui.py                        # Panels, symbols and input
tests/                          # unittest; no personal match logs
|-- test_dice.py
|-- test_scoring.py
|-- test_ai.py
|-- test_normal_ai.py
|-- test_simulation.py
|-- test_progression.py
|-- test_growth.py               # Economy and complete growth run
|-- test_gui.py                  # Snapshot isolation and complete mouse-driven run
|-- test_special_dice.py         # Weights, wildcards, fixed slots and AI
|-- test_effect_dice.py          # Momentum, Rescue, shared AI/growth/log rules
|-- test_event_screens.py        # Actual event animation/result snapshots
|-- test_run_score.py            # Score replay, income and Boss bounty
|-- test_leaderboard.py          # Read-only history ranking and malformed logs
|-- test_initial_rewards.py      # Three starting gifts and Silver-only Rescue
|-- test_match_log.py
|-- test_economy_analysis.py
`-- test_ui.py
docs/                           # Rules, designs and historical experiments
assets/gui/                     # Opening artwork and its source notes
match_logs/                     # Actual GUI/CLI opponent games only
tools/                          # Historical economy analysis
```

Start reviewing with `models.Die` and `dice.roll_item`, then
`scoring.turn_actions`, `battle.begin_roll` / `resolve_roll`, and finally
`progression.run_campaign`. The UI renders state; scoring has no input/output.
