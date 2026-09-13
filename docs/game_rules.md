# The King's Gambit: Dice Game Rules

## 1. Purpose and source

The dice game in *The King's Gambit* uses the basic Dice/Farkle rules found in
*Kingdom Come: Deliverance II*, adapted to the five-encounter structure in
[`game_design.md`](game_design.md).

The central decision is always:

> Bank the points earned during this turn, or roll again for more points and
> risk losing the entire unbanked turn score?

This document defines the normal rules before relics, special dice, opponent
abilities, or other modifiers are applied.

## 2. Match objective

- A match is played between the player and one opponent.
- The player and opponent take alternating turns.
- The first side to reach the match target wins the encounter.
- The Version 1 target is **2,000 points**, unless encounter balancing later
  assigns a different target to a particular opponent.
- Points earned during a turn are unbanked. They do not become part of the
  player's match score until the player banks them.

## 3. Turn sequence

1. Start the turn with an unbanked turn score of 0.
2. Roll all six available dice.
3. If the roll contains no scoring die or scoring combination, the player
   busts. The turn ends and all unbanked points from that turn are lost.
4. Otherwise, select at least one valid scoring die or combination from the
   current roll.
5. Add the selected score to the unbanked turn score and set the selected dice
   aside.
6. Choose one of the following actions:
   - **Bank:** add the unbanked turn score to the match score and end the turn.
   - **Roll again:** roll only the dice that were not set aside and continue
     the same turn.
7. After a turn ends, the opponent takes a turn under the same base rules.

A player may select more than one independent scoring group from the same
roll. For example, `1, 4, 4, 4, 5, 6` may score the single 1, three 4s, and the
single 5 for a total of 550 points.

Scoring combinations cannot be assembled across separate rolls. For example,
two 4s set aside from one roll cannot be combined with a 4 from a later roll
to make three 4s.

## 4. Scoring

### 4.1 Single scoring dice

| Dice | Score |
|---|---:|
| Single 1 | 100 |
| Single 5 | 50 |

Single 2s, 3s, 4s, and 6s do not score.

### 4.2 Three of a kind

| Combination | Score |
|---|---:|
| Three 1s | 1,000 |
| Three 2s | 200 |
| Three 3s | 300 |
| Three 4s | 400 |
| Three 5s | 500 |
| Three 6s | 600 |

### 4.3 Four, five, or six of a kind

Every matching die beyond the third doubles the combination's score.

| Face | Three | Four | Five | Six |
|---:|---:|---:|---:|---:|
| 1 | 1,000 | 2,000 | 4,000 | 8,000 |
| 2 | 200 | 400 | 800 | 1,600 |
| 3 | 300 | 600 | 1,200 | 2,400 |
| 4 | 400 | 800 | 1,600 | 3,200 |
| 5 | 500 | 1,000 | 2,000 | 4,000 |
| 6 | 600 | 1,200 | 2,400 | 4,800 |

### 4.4 Straights

| Combination | Score |
|---|---:|
| `1, 2, 3, 4, 5` | 500 |
| `2, 3, 4, 5, 6` | 750 |
| `1, 2, 3, 4, 5, 6` | 1,500 |

All dice in a straight must occur in the same roll.

## 5. Selection rules

- At least one scoring die or complete scoring combination must be selected
  after every successful roll.
- A non-scoring die cannot be selected by itself.
- An incomplete combination cannot be selected. For example, two 3s cannot be
  set aside in the hope of completing three 3s on a later roll.
- The player does not have to select every scoring die in a roll.
- The score validator must calculate only the dice selected from the current
  roll, not every scoring die that was rolled.
- Once selected dice are scored and set aside, they are not rolled again during
  that turn unless a later rule explicitly returns all dice to play.

## 6. Banking and busting

### Banking

Banking transfers the entire unbanked turn score to the player's match score
and ends the turn. Previously banked match points are never risked by rolling.

### Busting

A roll is a bust when none of the newly rolled dice can score under the active
rules. On a bust:

- the current turn ends immediately;
- the entire unbanked turn score becomes 0;
- the banked match score is unchanged; and
- play passes to the opponent.

## 7. Hot dice

Hot dice are enabled in Version 1. If all six dice have been scored during one
turn, all six dice become available again. The player may either bank or
continue the same turn by rolling all six dice. The accumulated unbanked turn
score remains at risk, and a bust after the new roll loses that entire score.

Scoring all six dice does not bank points, end the turn, or grant a separate
bonus.

## 8. Opponent banking behaviour

Each opponent has a configured **score ambition**, also called its banking
threshold. After selecting valid scoring dice, the opponent must:

- bank when its unbanked turn score reaches or exceeds its score ambition;
- continue rolling while below that score ambition; and
- bank immediately whenever its banked match score plus its current unbanked
  turn score reaches or exceeds the match target, regardless of its normal
  score ambition.

The basic AI is deterministic apart from dice rolls. It does not use machine
learning or hidden strategy rules.

## 9. Version 1 implementation scope

The initial scoring validator must support:

- single 1s;
- single 5s; and
- three of a kind.

Four-to-six of a kind and straights belong to the intended KCD2-inspired
ruleset, but should be enabled only after the initial validator is reliable and
covered by tests, as required by `game_design.md`.

Badges from *Kingdom Come: Deliverance II* are not part of the base rules.
Relics, special dice, and opponent abilities in *The King's Gambit* may later
modify these rules, but their effects must be documented separately and must
not be embedded in the base scoring implementation.

## 10. Examples

| Roll | Selected dice | Score | Valid? |
|---|---|---:|---|
| `1, 2, 3, 4, 5, 6` | `1, 5` | 150 | Yes |
| `2, 2, 2, 3, 4, 6` | `2, 2, 2` | 200 | Yes |
| `1, 4, 4, 4, 5, 6` | `1, 4, 4, 4, 5` | 550 | Yes |
| `2, 3, 3, 4, 6, 6` | none | 0 | Bust |
| `3, 3, 4, 4, 5, 6` | `3, 3` | 0 | No; an incomplete triple cannot score |

## 11. References

- [GameSpot: KCD2 Farkle guide and scoring system](https://www.gamespot.com/gallery/kingdom-come-deliverance-2-dice-game-farkle-tips-guide/2900-6189/)
- [GamesRadar+: KCD2 Dice rules and scoring combinations](https://www.gamesradar.com/games/action-rpg/kingdom-come-deliverance-2-dice-how-to-play/)

These references describe the source game's behaviour. Where this document
differs, the project-specific rules and scope in this document take priority.
