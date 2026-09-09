"""
State setters: choose where every fighter starts each episode.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple

from ..common_values import GROUND_Y, STAGE_X_MAX, STAGE_X_MIN

Position = Tuple[float, float]
ItemSpawn = Tuple[str, float, float]


class StateSetter(ABC):
    # spawn surface, overridden per-map by set_map_info(); defaults = small stage
    ground_y: float = GROUND_Y
    x_min: float = STAGE_X_MIN
    x_max: float = STAGE_X_MAX
    map_info: Optional[dict] = None

    def set_map_info(self, map_info: Optional[dict]) -> None:
        """
        Called by Match with the chosen map's static geometry (or None).

        Derives the spawnable floor from the map's longest solid horizontal segment (the main stage)
        """
        self.map_info = map_info
        if not map_info:
            return
        horiz = [(p1, p2) for p1, p2 in (map_info.get("hard") or [])
                 if p1[1] == p2[1]]
        if not horiz:
            return
        # longest horizontal solid; ties broken by SMALLER y (y grows downward, so that's
        # the TOP face - the main stage is a closed box and its underside is equally long)
        (x1, y), (x2, _) = max(horiz, key=lambda s: (abs(s[1][0] - s[0][0]), -s[0][1]))
        lo, hi = sorted((x1, x2))
        margin = min(150.0, 0.05 * (hi - lo))   # stay off the lip
        self.ground_y = float(y) - 1.0          # feet just above the surface
        self.x_min = lo + margin
        self.x_max = hi - margin

    # Clear every loose item off the stage and out of the fighters' hands at reset
    clear_items: bool = False

    @abstractmethod
    def build_positions(self, n_players: int) -> List[Position]:
        """One (x, y) per fighter, port-ordered."""

    def build_items(self, n_players: int) -> List[ItemSpawn]:
        """
        Items to put on the stage after the fighters are placed. Default: none.
        """
        return []

    def build_held(self, n_players: int, heroes: Sequence[int]) -> List[Optional[str]]:
        """
        Item each fighter starts holding, port-ordered. Default: none.
        """
        return [None] * n_players
