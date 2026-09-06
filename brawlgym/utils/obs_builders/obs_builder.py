"""
Observation builders: turn a GameState into per-agent observation vectors.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from ..gamestates import GameState, PlayerData


class ObsBuilder(ABC):
    map_info = None   # the chosen map's static geometry (bounds/hard/soft/respawn), or None

    def set_map_info(self, map_info) -> None:
        """
        Called by Match with the chosen map's static geometry (or None).

        DefaultObs ignores it currently; custom builders can encode distances to floors,
        platform layout, blastzone proximity, etc. from the segments.
        """
        self.map_info = map_info

    def reset(self, initial_state: GameState) -> None:
        """
        Called once per episode with the post-reset state.
        """

    @abstractmethod
    def build_obs(self, player: PlayerData, state: GameState, previous_action: Any) -> np.ndarray:
        """
        Observation for one agent.
        """
