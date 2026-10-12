# The King's Gambit

*The King's Gambit* is a short medieval dice roguelite inspired by the Dice
minigame in *Kingdom Come: Deliverance II*. The player faces five gamblers in a
fixed sequence and must decide when to keep rolling for a higher score and when
to bank points safely.

The project is being developed as a Python command-line game with an ASCII
gamebar. Version 1 is designed to use only the Python standard library.

## Project status

The dice-rule core, single-player practice and one Player-versus-Easy-AI match
are implemented and tested. Both modes share scoring, selection validation,
busts, banking, hot dice and a refreshed ASCII gamebar. Rewards, the shop, HP
and the five-encounter run are not implemented yet.

The revised scoring rules are implemented in the single-player practice mode:
three 1s = 500, matching dice beyond three add 200, and straights = 500/600/1,200.
Ordinary and consecutive three pairs, repeated hot dice, and legal zero-point
actions are supported. Banking at least 2,000 points ends practice with victory.
The opponent match alternates player and AI turns and ends immediately when
either side banks at least 2,000 points. Five-encounter progression, rewards
and HP remain future work; see [TODO.md](TODO.md).

The single-player gamebar shows the turn number, phase, banked score and target,
unbanked points, latest dice, selected positions, available dice, commands and
result messages. It refreshes in place in an interactive terminal; redirected
output and automated tests retain readable frames instead of clearing the screen.
Scoring rules appear in a separate box at the top, immediately followed by
the gamebar. Both boxes are 66 columns wide and fit a standard 80-column
terminal without the wrapping caused by the earlier side-by-side layout.

## Basic game rules

- Before each opponent match, one fair 0/1 roll chooses who starts:
  0 = AI, 1 = Player. The gamebar keeps the result visible. It is not a scoring
  die and is not repeated between turns. Solo practice skips this roll.
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
[`docs/game_rules.md`](docs/game_rules.md) for the complete scoring table,
selection rules, and examples.

## Run structure

A complete run contains five encounters:

1. Normal opponent, followed by a reward.
2. Normal opponent, followed by a shop.
3. Elite opponent, followed by a reward.
4. Strong opponent, followed by a rest or shop.
5. Boss encounter.

The player starts a run with 3 HP. Losing an encounter removes 1 HP. Reaching
0 HP ends the run, while defeating the boss wins the run.

## Opponents

Each opponent has a score ambition that controls its risk level. The opponent
continues rolling while below this amount and banks once its unbanked score
reaches or exceeds it. An opponent always banks immediately if doing so would
win the match.

Easy AI uses the highest immediate scoring legal action. Equal-score choices
use the lexicographically earliest ascending position list. The default
score ambition is 500, a starting value for testing rather than final balance.
Its rolls, selected positions, score gains, Hot Dice and Bank/Roll reasons are
shown in sequence. Each action pauses for 2 seconds; Enter advances between
completed turns. Ctrl-C exits during AI playback without banking risked points.
Future utility and win-probability AI are research directions, not V1 requirements.
The AI is intended to be deterministic and easy to understand. It does not use
machine learning.

## Planned features

- A continuously updated ASCII gamebar.
- Five opponents with different risk levels.
- Rewards chosen from three options.
- Relics and special dice that modify rolling, scoring, banking, or survival.
- Gold and one simple shop.
- Healing, victory, and defeat screens.
- Safe handling of invalid player input.
- Automated tests for scoring and game-state changes.

Version 1 does not include multiplayer, map exploration, permanent progression,
or a large inventory system.

## Requirements

- Python 3.10 or newer is recommended.
- No third-party packages are required for the planned command-line version.

## Running the game

Run one match against Easy AI from the project directory with:

```powershell
python main.py
```

For the original single-player practice mode, use:

```powershell
python main.py --practice
```

To change the AI reading time and ambition, for example:

```powershell
python main.py --ai-delay 3 --ambition 500
```

`--ai-delay 0` removes timed pauses; completed turns still wait for Enter.
The delay must be finite and non-negative; ambition must be a positive integer.

Enter positions such as `1 3 5` to select dice, then `R` to roll or `B` to bank.
After a completed turn, press Enter to start the next turn or Q to quit.
For ordinary three pairs, selecting all six positions explicitly activates a
zero-point reroll; there is no Bank prompt before that reroll. Selecting only
scoring 1s/5s instead remains possible. `Q`, EOF, or Ctrl-C exits the practice.

`battle.run_match()` and `battle.run_practice()` share the same turn loop.
`models.MatchState` tracks both scores, the active side and winner. `ui.py` only renders
frames and parses input; scoring and state changes stay in the core modules.

## Match records / 对局记录

`python main.py` automatically saves your opponent match as a UTF-8 text file
in `match_logs/`, named by the local start time, for example
`2026-10-08_15-30-20_123456.txt`. Microseconds distinguish starts within one
second; existing records are never overwritten. The saved path is printed
when the match ends or you quit.

Each event records the turn number, acting side, dice in positional order,
selected positions, available dice, phase, both banked scores, the acting
side's current banked score and unbanked turn score. AI Bank/Roll reasons,
Hot Dice, ordinary three pairs, Bust losses and the winner or early exit are
included. Events are flushed immediately, so earlier actions survive an
interruption. On quit, any displayed unbanked points are discarded, not banked.

Only CLI opponent matches are saved. Practice and direct `run_match()` calls
(including automated tests/simulations) do not create personal records.
Logging tests use temporary directories, not `match_logs/`. Records remain
local and are ignored by Git; there is no upload or automatic deletion.

## Running tests

Run the automated tests with:

```powershell
python -m unittest discover -s tests
```

## Documentation

- [Game design](docs/game_design.md) — concept, scope, run structure, UI, and
  completion criteria.
- [Game rules](docs/game_rules.md) — exact scoring and turn rules.
- [Scoring and AI reference](docs/scoring_and_ai_reference.md) — archived source;
  statistical claims await independent reproduction.
- [Project to-do list](TODO.md) — unresolved decisions and development work.
- [Agent guidance](AGENTS.md) — implementation boundaries and quality
  requirements.

## Planned project structure

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

The remaining modules will be created incrementally as Version 1 is
implemented.
