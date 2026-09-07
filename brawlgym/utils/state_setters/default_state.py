"""
State setters: choose where every fighter starts each episode.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .state_setter import Position, StateSetter


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
