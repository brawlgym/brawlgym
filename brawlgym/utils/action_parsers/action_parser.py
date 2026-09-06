"""
Action parsers: turn agent actions into per-fighter input masks.

The engine takes one input bitmask per fighter per step.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Sequence

import numpy as np

from ..gamestates import GameState

# input bits (engine-level)
# TODO: more research should be done on the exact semantics of these bits and how they interact with each other
UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8
JUMP, LIGHT, HEAVY, DODGE, THROW = 16, 64, 128, 256, 512


class ActionParser(ABC):
    """
    Maps whatever your policy outputs to engine input masks.
    """

    @abstractmethod
    def get_action_space_size(self) -> int:
        """
        Length of one agent's action vector.
        """

    @abstractmethod
    def parse_actions(self, actions: Sequence[Any], state: GameState) -> List[int]:
        """
        actions[i] -> input mask for fighter i. Must return one mask per fighter.
        """
