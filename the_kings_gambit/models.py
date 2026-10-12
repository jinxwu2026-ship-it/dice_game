"""Small state objects used by the dice-rule core."""


class TurnState:
    """Track scores and available dice during one turn.

    Scoring is calculated elsewhere. This class only applies valid state
    changes after a selection, bank, or bust.
    """

    def __init__(self, match_score=0, target=2000):
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
        self.unbanked_score = 0
        self.dice_available = 0
        self.is_active = False
        self.phase = "ended"
        self.current_roll = None

    def bank(self):
        """Transfer unbanked points to the match score and end the turn."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        if self.phase != "decision":
            raise ValueError("banking is allowed only after a positive selection")
        if self.unbanked_score == 0:
            raise ValueError("there are no points to bank")

        # Banking is the only operation that makes turn points safe.
        self.match_score += self.unbanked_score
        self.unbanked_score = 0
        self.dice_available = 0
        self.is_active = False
        self.phase = "ended"
        self.current_roll = None


class MatchState:
    """Keep each side's banked score and choose whose turn comes next."""

    def __init__(self, against_ai=True, target=2000):
        # Reuse the turn's target validation rather than defining another rule.
        self.target = TurnState(target=target).target
        self.scores = {"Player": 0, "Opponent": 0}
        self.active_side = "Player"
        self.starting_roll = None  # Practice needs no opening roll.
        self.turn_number = 1
        self.against_ai = against_ai
        self.winner = None

    def start_turn(self):
        if self.winner is not None:
            raise ValueError("the match has already ended")
        return TurnState(self.scores[self.active_side], self.target)

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
