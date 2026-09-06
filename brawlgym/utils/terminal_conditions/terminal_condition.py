"""
Terminal conditions: decide when an episode ends.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..gamestates import GameState


class TerminalCondition(ABC):
    def reset(self, initial_state: GameState) -> None:
        """
        Called once per episode with the post-reset state.
        """

    @abstractmethod
    def is_terminal(self, current_state: GameState) -> bool:
        """
        True ends the episode after this step.
        """
