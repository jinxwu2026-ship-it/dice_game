"""Small state objects used by the dice-rule core."""


class TurnState:
    """Track scores and available dice during one turn.

    Scoring is calculated elsewhere. This class only applies valid state
    changes after a selection, bank, or bust.
    """

    def __init__(self, match_score=0):
        if not isinstance(match_score, int) or isinstance(match_score, bool):
            raise ValueError("match_score must be an integer")
        if match_score < 0:
            raise ValueError("match_score cannot be negative")

        self.match_score = match_score
        self.unbanked_score = 0
        self.dice_available = 6
        self.is_active = True

    def add_selection(self, selection_score, number_of_selected_dice):
        """Add valid points and return 'hot_dice' or 'scored'."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
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
        if number_of_selected_dice == self.dice_available:
            # All currently available dice have scored. Hot Dice returns all
            # six dice without banking or clearing the accumulated points.
            self.dice_available = 6
            return "hot_dice"

        self.dice_available -= number_of_selected_dice
        return "scored"

    def bust(self):
        """Lose unbanked points and end the turn without changing match score."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        # Only the points from this turn are lost. Previously banked match
        # points are deliberately left unchanged.
        self.unbanked_score = 0
        self.dice_available = 0
        self.is_active = False

    def bank(self):
        """Transfer unbanked points to the match score and end the turn."""
        if not self.is_active:
            raise ValueError("the turn has already ended")
        if self.unbanked_score == 0:
            raise ValueError("there are no points to bank")

        # Banking is the only operation that makes turn points safe.
        self.match_score += self.unbanked_score
        self.unbanked_score = 0
        self.dice_available = 0
        self.is_active = False
