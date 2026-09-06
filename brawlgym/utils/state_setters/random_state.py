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


class RandomStateSetter(StateSetter):
    """
    Uniform random on-stage spawns; optionally with random air spawns for recovery play.
    """

    def __init__(self, allow_air: bool = False, min_gap: float = 200.0,
                 rng: Optional[random.Random] = None):
        self.allow_air = allow_air
        self.min_gap = min_gap
        self.rng = rng or random.Random()

    def build_positions(self, n_players: int) -> List[Position]:
        xs: List[float] = []
        for _ in range(n_players):
            for _attempt in range(50):
                x = self.rng.uniform(self.x_min, self.x_max)
                if all(abs(x - other) >= self.min_gap for other in xs):
                    break
            xs.append(x)
        out: List[Position] = []
        for x in xs:
            y = self.ground_y
            if self.allow_air and self.rng.random() < 0.5:
                y = self.rng.uniform(self.ground_y - 900.0, self.ground_y - 200.0)
            out.append((x, y))
        return out
