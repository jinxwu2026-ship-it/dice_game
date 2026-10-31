"""Small state objects used by the dice-rule core."""

from dataclasses import dataclass, field
from itertools import count


DIE_KINDS = ("basic", "lucky", "two", "odd", "even", "devil", "angel", "momentum", "rescue")
QUALITIES = ("bronze", "silver", "gold")
_die_ids = count(1)


@dataclass(frozen=True)
class Die:
    """An individual item; identical effects still have different identities."""

    kind: str = "basic"
    quality: str = "basic"
    serial: int = field(default_factory=lambda: next(_die_ids), init=False)

    def __post_init__(self):
        if self.kind not in DIE_KINDS:
            raise ValueError("unknown die kind")
        if (self.kind == "basic") != (self.quality == "basic"):
            raise ValueError("basic dice have no special quality")
        if self.kind != "basic" and self.quality not in QUALITIES:
            raise ValueError("unknown die quality")
        if self.kind in ("devil", "angel") and self.quality != "silver":
            raise ValueError("unique wildcard dice are always Silver")
        if self.kind == "rescue" and self.quality != "silver":
            raise ValueError("rescue dice are always Silver")


def validate_roster(dice):
    if not isinstance(dice, (list, tuple)) or len(dice) != 6:
        raise ValueError("a roster must contain six dice")
    if not all(isinstance(die, Die) for die in dice):
        raise ValueError("a roster contains Die items")
    if len({die.serial for die in dice}) != 6:
        raise ValueError("the same physical die cannot occupy two slots")
    for kind in ("devil", "angel"):
        if sum(die.kind == kind for die in dice) > 1:
            raise ValueError("only one of each unique wildcard may exist")
    if sum(die.kind == "rescue" for die in dice) > 1:
        raise ValueError("equip at most one rescue die")


class TurnState:
    """Track scores and available dice during one turn.

    Scoring is calculated elsewhere. This class only applies valid state
    changes after a selection, bank, or bust.
    """

    def __init__(self, match_score=0, target=2000, dice=None, ability_budget=None):
        if not isinstance(match_score, int) or isinstance(match_score, bool):
            raise ValueError("match_score must be an integer")
        if match_score < 0:
            raise ValueError("match_score cannot be negative")
        if not isinstance(target, int) or isinstance(target, bool) or target <= 0:
            raise ValueError("target must be a positive integer")

        self.match_score = match_score
        self.unbanked_score = 0
        self.dice_available = 6
        self.target = target
        self.is_active = match_score < target
        if not self.is_active:
            self.dice_available = 0
        self.phase = "ready" if self.is_active else "ended"
        self.current_roll = None
        if dice is not None:
            validate_roster(dice)
        self.dice = tuple(dice) if dice is not None else None
        self.available_slots = list(range(6)) if self.is_active else []
        self.roll_slots = []
        self.held_faces = {}
        self.hot_dice_faces = {}  # Preserve the completed tray until the next roll.
        self.last_mapping = {}
        self.successes = 0
        self.last_base = self.last_bonus = 0
        self.outcome = ""
        self.lost_score = self.banked_points = 0
        self.ability_budget = ability_budget if ability_budget is not None else {
            "rescue": int(dice is not None and any(d.kind == "rescue" for d in dice))}

    @property
    def can_rescue(self):
        return (self.is_active and self.ability_budget["rescue"] > 0 and self.dice is not None
                and any(self.dice[i].kind == "rescue" for i in self.available_slots))

    @property
    def has_won(self):
        """Only banked points can meet the match target."""
        return self.match_score >= self.target

    def add_selection(self, selection_score, number_of_selected_dice):
        """Add valid points and return 'hot_dice' or 'scored'."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        if self.phase != "select":
            raise ValueError("roll and select dice before adding points")
        if not isinstance(selection_score, int) or isinstance(selection_score, bool):
            raise ValueError("selection_score must be an integer")
        if selection_score <= 0:
            raise ValueError("selection_score must be positive")
        if (
            not isinstance(number_of_selected_dice, int)
            or isinstance(number_of_selected_dice, bool)
            or number_of_selected_dice < 1
            or number_of_selected_dice > self.dice_available
        ):
            raise ValueError("selected dice must be available in this roll")

        # Points remain at risk until bank() is called.
        self.unbanked_score += selection_score
        self.successes += 1
        self.current_roll = None
        self.phase = "decision"
        if number_of_selected_dice == self.dice_available:
            # All currently available dice have scored. Hot Dice returns all
            # six dice without banking or clearing the accumulated points.
            self.dice_available = 6
            return "hot_dice"

        self.dice_available -= number_of_selected_dice
        return "scored"

    def activate_pairs(self):
        """Apply a validated ordinary-pair action; banking is not available."""
        if not self.is_active or self.phase != "select" or self.dice_available != 6:
            raise ValueError("ordinary pairs require a pending six-die roll")
        self.current_roll = None
        self.dice_available = 6
        self.phase = "ready"
        return "ordinary_pairs"

    def bust(self):
        """Lose unbanked points and end the turn without changing match score."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        # Only the points from this turn are lost. Previously banked match
        # points are deliberately left unchanged.
        self.lost_score = self.unbanked_score
        self.outcome = "bust"
        self.unbanked_score = 0
        self.successes = 0
        self.dice_available = 0
        self.is_active = False
        self.phase = "ended"
        self.current_roll = None
        self.available_slots = []

    def bank(self):
        """Transfer unbanked points to the match score and end the turn."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        if self.phase != "decision":
            raise ValueError("banking is allowed only after a positive selection")
        if self.unbanked_score == 0:
            raise ValueError("there are no points to bank")

        # Banking is the only operation that makes turn points safe.
        self.banked_points = self.unbanked_score
        self.outcome = "bank"
        self.match_score += self.unbanked_score
        self.unbanked_score = 0
        self.successes = 0
        self.dice_available = 0
        self.is_active = False
        self.phase = "ended"
        self.current_roll = None
        self.available_slots = []


class MatchState:
    """Keep each side's banked score and choose whose turn comes next."""

    def __init__(self, against_ai=True, target=2000, rosters=None):
        # Reuse the turn's target validation rather than defining another rule.
        self.target = TurnState(target=target).target
        self.scores = {"Player": 0, "Opponent": 0}
        self.active_side = "Player"
        self.starting_roll = None  # Practice needs no opening roll.
        self.turn_number = 1
        self.against_ai = against_ai
        self.winner = None
        self.rosters = rosters
        if rosters is not None:
            items = []
            for side in ("Player", "Opponent"):
                validate_roster(rosters[side])
                items.extend(rosters[side])
            if len({die.serial for die in items}) != 12:
                raise ValueError("opponents cannot share physical dice")
            for kind in ("devil", "angel"):
                if sum(die.kind == kind for die in items) > 1:
                    raise ValueError("a unique wildcard cannot exist on both sides")
        self.ability_budgets = {side: {"rescue": int(rosters is not None and any(
            die.kind == "rescue" for die in rosters[side]))} for side in self.scores}

    def start_turn(self):
        if self.winner is not None:
            raise ValueError("the match has already ended")
        dice = self.rosters[self.active_side] if self.rosters is not None else None
        return TurnState(self.scores[self.active_side], self.target, dice,
                         self.ability_budgets[self.active_side])

    def finish_turn(self, state):
        """Save banked points, check victory, then alternate if necessary."""
        if self.winner is not None or state.is_active:
            raise ValueError("finish an active turn before changing sides")
        self.scores[self.active_side] = state.match_score
        if state.has_won:
            self.winner = self.active_side
            return
        if self.against_ai:
            self.active_side = "Opponent" if self.active_side == "Player" else "Player"
        self.turn_number += 1


class RunState:
    """Keep campaign state; HP counts extra lives, not the current life."""

    def __init__(self, target=2000):
        self.target = TurnState(target=target).target
        self.hp = 1
        self.encounter_index = 0
        self.status = "active"
        self.history = []
        self.score_history = []
        self.score_summary = None
        self.coins = 100
        self.dice = [Die() for _ in range(6)]
        self.spawned_unique = set()
        self.notice = ""
        self.end_reason = ""

    @property
    def is_active(self):
        return self.status == "active"
