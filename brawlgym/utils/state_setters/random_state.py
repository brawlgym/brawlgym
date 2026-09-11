"""
State setters: choose where every fighter starts each episode.
"""
from __future__ import annotations

import random
from typing import List, Optional

import numpy as np

from .. import math
from .state_setter import Position, StateSetter


class RandomStateSetter(StateSetter):
    """
    Uniform random on-stage spawns; optionally with random air spawns for recovery play.
    """

    MAX_TRIES = 200

    def __init__(self, allow_air: bool = False, anywhere: bool = False, min_gap: float = 200.0,
                 rng: Optional[random.Random] = None):
        """
        :param allow_air: Half the spawns are put in the air over the stage instead of on it.
        :param anywhere: Spawn uniformly anywhere inside the blast bounds - over the stage, off
                         the side, under it - skipping only points inside solid geometry. Takes
                         precedence over allow_air, and needs map geometry: without it the
                         fighters spawn on the ground as usual.
        :param min_gap: Keep fighters this far apart, along x on the ground and as a straight
                        line distance when spawning anywhere.
        """
        self.allow_air = allow_air
        self.anywhere = anywhere
        self.min_gap = min_gap
        self.rng = rng or random.Random()
        self._hard = np.zeros((0, 2, 2))
        self._blast = None

    def set_map_info(self, map_info) -> None:
        super().set_map_info(map_info)
        map_info = map_info or {}
        self._hard = np.asarray(map_info.get("hard") or [], dtype=np.float64).reshape(-1, 2, 2)
        bounds = map_info.get("bounds")
        if bounds:
            x, y, w, h = bounds["X"], bounds["Y"], bounds["W"], bounds["H"]
            self._blast = (x, y, x + w, y + h)
        else:
            self._blast = None

    def build_positions(self, n_players: int) -> List[Position]:
        if self.anywhere and self._blast is not None:
            return self._blast_zone_positions(n_players)
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

    def _blast_zone_positions(self, n_players: int) -> List[Position]:
        """
        Rejection sampling over the whole blast zone, falling back to a ground spawn if the
        draws keep landing inside the stage or on top of someone.
        """
        x0, y0, x1, y1 = self._blast
        out: List[Position] = []
        for _ in range(n_players):
            spawn = None
            for _attempt in range(self.MAX_TRIES):
                pos = (self.rng.uniform(x0, x1), self.rng.uniform(y0, y1))
                if self._in_solid(pos) or not self._clears(pos, out):
                    continue
                spawn = pos
                break
            if spawn is None:
                spawn = (self.rng.uniform(self.x_min, self.x_max), self.ground_y)
            out.append(spawn)
        return out

    def _in_solid(self, pos: Position) -> bool:
        return bool(math.inside_segments([pos], self._hard)[0])

    def _clears(self, pos: Position, others: List[Position]) -> bool:
        return all(math.vecmag(np.subtract(pos, other)) >= self.min_gap for other in others)
