"""
Action parsers: turn agent actions into per-fighter input masks.

The engine takes one input bitmask per fighter per step. Inputs are applied with correct
edge semantics (a held button re-triggers exactly like a human re-pressing it would).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Sequence

import numpy as np

from ..gamestates import GameState

# input bits (engine-level)
UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8
JUMP, LIGHT, HEAVY, DODGE, THROW = 16, 64, 128, 256, 512


from .action_parser import ActionParser


class DefaultAction(ActionParser):
    """
    8 binary buttons per agent: [left, right, up, down, jump, light, heavy, dodge].

    Left+right (or up+down) together cancel out. Anything >0.5 counts as pressed, so both
    discrete {0,1} and continuous policies work unchanged.
    """

    BUTTONS = (LEFT, RIGHT, UP, DOWN, JUMP, LIGHT, HEAVY, DODGE)

    def get_action_space_size(self) -> int:
        return len(self.BUTTONS)

    def parse_actions(self, actions: Sequence[Any], state: GameState) -> List[int]:
        masks: List[int] = []
        for a in actions:
            v = np.asarray(a, dtype=np.float32).reshape(-1)
            mask = 0
            for j, bit in enumerate(self.BUTTONS):
                if j < v.shape[0] and v[j] > 0.5:
                    mask |= bit
            if (mask & LEFT) and (mask & RIGHT):
                mask &= ~(LEFT | RIGHT)
            if (mask & UP) and (mask & DOWN):
                mask &= ~(UP | DOWN)
            masks.append(mask)
        return masks
