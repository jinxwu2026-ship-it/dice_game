# The King's Gambit

*The King's Gambit* is a short medieval dice roguelite inspired by the Dice
minigame in *Kingdom Come: Deliverance II*. The player faces five gamblers in a
fixed sequence and must decide when to keep rolling for a higher score and when
to bank points safely.

The project is being developed as a Python command-line game with an ASCII
gamebar. Version 1 is designed to use only the Python standard library.

## Project status

The dice-rule core and a single-player CLI practice mode are implemented and
tested. Practice mode includes dice rolling, scoring, selection validation,
busts, banking, and hot dice. AI, rewards, the shop, encounters, and the
complete playable flow are not implemented yet.

## Basic game rules

- The player and opponent take alternating turns.
- A turn begins by rolling six dice.
- The player selects at least one valid scoring die or combination.
- Selected points are added to the unbanked turn score.
- The player may bank the score and end the turn, or roll the remaining dice
  and risk the unbanked points.
- A roll with no scoring dice is a bust. All unbanked points from that turn are
  lost.
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
| Three 1s | 1,000 |
| Three 2s | 200 |
| Three 3s | 300 |
| Three 4s | 400 |
| Three 5s | 500 |
| Three 6s | 600 |

Later scoring support includes four-to-six of a kind and straights. See
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

The entry point will be `main.py`. Once the basic playable version has been
implemented, run it from the project directory with:

```powershell
python main.py
```

At the current project stage, this command starts a single-player dice practice
mode rather than the complete five-encounter game.

## Running tests

Run the automated tests with:

```powershell
python -m unittest discover -s tests
```

## Documentation

- [Game design](docs/game_design.md) — concept, scope, run structure, UI, and
  completion criteria.
- [Game rules](docs/game_rules.md) — exact scoring and turn rules.
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
