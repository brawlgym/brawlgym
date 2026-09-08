"""
Action parsers: turn agent actions into per-fighter input masks.

The engine takes one input bitmask per fighter per step.
"""
from __future__ import annotations

from typing import Any, List, Optional, Sequence

import numpy as np

from ..common_values import DODGE, DOWN, HEAVY, JUMP, LEFT, LIGHT, RIGHT
from ..gamestates import GameState
from .action_parser import ActionParser, mask_to_name


class LookupAction(ActionParser):
    """
    One discrete action per agent: an index into a table of input masks.

    The default table covers movement, jumps, every unarmed attack direction and dodges.
    Pass your own list of masks (combine the bits from action_parser) to change the set.
    """

    DEFAULT_TABLE = (
        0,                  
        LEFT,
        RIGHT,
        JUMP,
        LEFT | JUMP,
        RIGHT | JUMP,
        LIGHT,
        LEFT | LIGHT,
        RIGHT | LIGHT,
        DOWN | LIGHT,
        HEAVY,
        LEFT | HEAVY,
        RIGHT | HEAVY,
        DOWN | HEAVY,
        DODGE,
        LEFT | DODGE,
        RIGHT | DODGE,
        DOWN | DODGE,
    )

    def __init__(self, table: Optional[Sequence[int]] = None):
        self.table: List[int] = [int(m) for m in (table if table is not None else self.DEFAULT_TABLE)]

    @property
    def n_actions(self) -> int:
        return len(self.table)

    @property
    def action_names(self) -> List[str]:
        return [mask_to_name(m) for m in self.table]

    def get_action_space_size(self) -> int:
        return 1

    def parse_actions(self, actions: Sequence[Any], state: GameState) -> List[int]:
        masks: List[int] = []
        for a in actions:
            idx = int(np.asarray(a).reshape(-1)[0])
            masks.append(self.table[idx])
        return masks
