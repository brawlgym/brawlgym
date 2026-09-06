"""
Observation builders: turn a GameState into per-agent observation vectors.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from ..gamestates import GameState, PlayerData


from .obs_builder import ObsBuilder


class DefaultObs(ObsBuilder):
    """
    Simple normalized observation.

    Per fighter (self first, then teammates, then opponents, port-ordered):
      [x, y, vx, vy, facing, on_ground, damage, dead, dodge_cd, jumps_used]  (10 features)
    plus the previous action appended for the observed agent.
    """

    POS_SCALE = 1.0 / 2000.0
    VEL_SCALE = 1.0 / 50.0
    DMG_SCALE = 1.0 / 300.0
    CD_SCALE = 1.0 / 3000.0
    # TODO: items, map, etc

    def _feats(self, p: PlayerData) -> list:
        return [
            p.x * self.POS_SCALE, p.y * self.POS_SCALE,
            p.vx * self.VEL_SCALE, p.vy * self.VEL_SCALE,
            -1.0 if p.facing_left else 1.0,
            1.0 if p.on_ground else 0.0,
            p.damage * self.DMG_SCALE,
            1.0 if p.dead else 0.0,
            p.dodge_cooldown * self.CD_SCALE,
            p.jumps_used / 3.0,
        ]

    def build_obs(self, player: PlayerData, state: GameState, previous_action: Any) -> np.ndarray:
        obs = self._feats(player)
        for p in sorted(state.teammates_of(player), key=lambda q: q.port):
            obs += self._feats(p)
        for p in sorted(state.opponents_of(player), key=lambda q: q.port):
            obs += self._feats(p)
        if previous_action is not None:
            obs += list(np.asarray(previous_action, dtype=np.float32).reshape(-1))
        return np.asarray(obs, dtype=np.float32)
