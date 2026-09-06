"""
State setters: choose where every fighter starts each episode.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

Position = Tuple[float, float]

# TODO: constants file
# default (small brawlhaven) stage reference values - conservative bounds, safely on the floor
GROUND_Y = 1849.0
STAGE_X_MIN, STAGE_X_MAX = 600.0, 2150.0


from .state_setter import StateSetter


class DefaultStateSetter(StateSetter):
    """
    Fixed, symmetric ground spawns spread across the stage.
    """

    def build_positions(self, n_players: int) -> List[Position]:
        if n_players <= 1:
            return [((self.x_min + self.x_max) / 2, self.ground_y)]
        span = self.x_max - self.x_min
        return [(self.x_min + span * i / (n_players - 1), self.ground_y)
                for i in range(n_players)]
