"""
Agents: anything other than the learning policy that can occupy a fighter for an episode.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..common_values import BOT_MEDIUM, BOT_OFF
from ..gamestates import GameState


class PretrainedAgent(ABC):
    """
    One fighter's controller for an episode, in place of the policy being trained.

    Two kinds exist. One supplies an action every step, which act() returns. The other is driven
    inside the game and supplies nothing, which act() signals by returning None; take_over() is
    where that kind arranges the handover.
    """

    def take_over(self, match, fighter: int) -> None:
        """
        Called once per episode, at reset, when this agent is given `fighter`.
        """

    def act(self, state: GameState, player_index: int) -> Optional[Any]:
        """
        This fighter's action for the current step, in the match's action space, or None when the
        game itself is supplying the inputs.
        """
        return None


class HardcodedAgent(PretrainedAgent):
    """
    An external controller that chooses an action each step.

    act() returns whatever the match's action parser accepts, which for LookupAction is one index
    into its table.
    """

    @abstractmethod
    def act(self, state: GameState, player_index: int) -> Any:
        raise NotImplementedError


class BuiltInAgent(PretrainedAgent):
    """
    The game's own AI, at one of its difficulty levels.

    It writes the fighter's inputs inside the game, so act() supplies nothing. Levels are in
    common_values, BOT_PUSHOVER through BOT_CHOSEN.
    """

    def __init__(self, difficulty: int = BOT_MEDIUM):
        if int(difficulty) == BOT_OFF:
            raise ValueError("BOT_OFF leaves the fighter without a controller; "
                             "pick a level from common_values.BOT_LEVELS")
        self.difficulty = int(difficulty)

    def take_over(self, match, fighter: int) -> None:
        match.set_bot(fighter, self.difficulty)

    def __repr__(self) -> str:
        from ..common_values import BOT_LEVEL_NAMES
        return "BuiltInAgent(%s)" % BOT_LEVEL_NAMES.get(self.difficulty, self.difficulty)
