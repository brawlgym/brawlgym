"""
Reward functions. Each gets the live GameState every step, per agent.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from ..gamestates import GameState, PlayerData


class RewardFunction(ABC):
    def reset(self, initial_state: GameState) -> None:
        """
        Called once per episode with the post-reset state.
        """

    @abstractmethod
    def get_reward(self, player: PlayerData, state: GameState, previous_action: Any) -> float:
        """
        Reward for one agent for the step that produced `state`.
        """
