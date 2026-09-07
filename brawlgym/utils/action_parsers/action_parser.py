"""
Action parsers: turn agent actions into per-fighter input masks.

The engine takes one input bitmask per fighter per step.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Sequence

import numpy as np

from ..common_values import BUTTON_BITS, DODGE, DOWN, HEAVY, JUMP, LEFT, LIGHT, RIGHT, THROW, UP
from ..gamestates import GameState


def mask_to_buttons(mask: int) -> np.ndarray:
    """
    Engine input mask -> one 0/1 entry per button, in BUTTON_BITS order.
    """
    return np.array([1.0 if mask & bit else 0.0 for bit in BUTTON_BITS], dtype=np.float32)


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
