import numpy as np
from typing import Any, List

from .. import common_values, math
from ..gamestates import GameState, PlayerData
from .obs_builder import ObsBuilder


class DefaultObs(ObsBuilder):
    """
    Relative observation with stage awareness.

    Positions are expressed inside the map's blast bounds (center 0, edges at +/-1) so the same
    policy reads any map; everyone else is also given relative to the observed fighter. The
    stage itself is sensed with rays cast from the fighter: each ray reports how close the nearest
    hard (solid) and soft (drop-through) surface is, 1 = touching, 0 = nothing within range.
    Ground probes look straight down from fixed offsets either side of the fighter, so the
    distance to the edge of the platform underfoot is read directly.

    Layout: [previous buttons, blast-edge distances, rays (hard), rays (soft), ground probes,
             self, teammates (port order), opponents (port order)].
    """

    GROUND_PROBE_OFFSETS = (-1000.0, -500.0, -250.0, -100.0, 100.0, 250.0, 500.0, 1000.0)

    def __init__(self, n_rays: int = 16, ray_range: float = 2000.0,
                 pos_std: float = common_values.POS_STD,
                 vel_std: float = common_values.VEL_STD,
                 damage_std: float = common_values.DAMAGE_STD):
        """
        :param n_rays: Rays cast around the fighter to sense the stage.
        :param ray_range: Distance in px beyond which a ray reports nothing.
        :param pos_std: Position normalization coefficient for relative positions.
        :param vel_std: Velocity normalization coefficient.
        :param damage_std: Damage normalization coefficient.
        """
        super().__init__()
        self.n_rays = n_rays
        self.ray_range = float(ray_range)
        self.POS_STD = pos_std
        self.VEL_STD = vel_std
        self.DAMAGE_STD = damage_std
        self._ray_dirs = math.ray_directions(n_rays)
        self._probe_offsets = np.array([[dx, -1.0] for dx in self.GROUND_PROBE_OFFSETS])
        self._probe_dirs = np.tile([[0.0, 1.0]], (len(self.GROUND_PROBE_OFFSETS), 1))
        self._floors = np.zeros((0, 2, 2))
        self._hard = np.zeros((0, 2, 2))
        self._soft = np.zeros((0, 2, 2))
        self._center = None
        self._half = None
        self._bounds = None

    def set_map_info(self, map_info) -> None:
        super().set_map_info(map_info)
        self._hard = np.asarray(map_info.get("hard") or [], dtype=np.float64).reshape(-1, 2, 2) if map_info else np.zeros((0, 2, 2))
        self._soft = np.asarray(map_info.get("soft") or [], dtype=np.float64).reshape(-1, 2, 2) if map_info else np.zeros((0, 2, 2))
        self._floors = np.concatenate([self._hard, self._soft])
        bounds = (map_info or {}).get("bounds")
        if bounds:
            x, y, w, h = bounds["X"], bounds["Y"], bounds["W"], bounds["H"]
            self._bounds = (x, y, x + w, y + h)
            self._center = np.array([x + w / 2.0, y + h / 2.0])
            self._half = np.array([w / 2.0, h / 2.0])
        else:
            self._bounds = self._center = self._half = None

    def reset(self, initial_state: GameState):
        pass

    def build_obs(self, player: PlayerData, state: GameState, previous_action: np.ndarray) -> Any:
        obs = [np.asarray(previous_action, dtype=np.float32).reshape(-1),
               self._blast_distances(player),
               self._rays(player, self._hard),
               self._rays(player, self._soft),
               self._ground_probes(player)]

        self._add_player_to_obs(obs, player)

        allies = []
        enemies = []

        for other in state.players:
            if other.port == player.port:
                continue

            if other.team == player.team:
                team_obs = allies
            else:
                team_obs = enemies

            self._add_player_to_obs(team_obs, other)

            # Extra info
            team_obs.extend([
                np.array([other.x - player.x, other.y - player.y]) / self.POS_STD,
                np.array([other.vx - player.vx, other.vy - player.vy]) / self.VEL_STD
            ])

        obs.extend(allies)
        obs.extend(enemies)
        return np.concatenate(obs).astype(np.float32)

    def _add_player_to_obs(self, obs: List, player: PlayerData):
        obs.extend([
            self._position(player),
            np.array([player.vx, player.vy]) / self.VEL_STD,
            [-1.0 if player.facing_left else 1.0,
             int(player.on_ground),
             player.damage / self.DAMAGE_STD,
             int(player.dodge_cooldown),
             int(player.dodging),
             player.jumps_used / common_values.MAX_JUMPS,
             int(player.has_weapon),
             int(player.dead)]])

    def _position(self, player: PlayerData) -> np.ndarray:
        pos = np.array([player.x, player.y])
        if self._center is None:
            return pos / self.POS_STD
        return (pos - self._center) / self._half

    def _blast_distances(self, player: PlayerData) -> np.ndarray:
        """
        Distance to the left, right, top and bottom blast edges.
        """
        if self._bounds is None:
            return np.zeros(4)
        x0, y0, x1, y1 = self._bounds
        return np.array([player.x - x0, x1 - player.x, player.y - y0, y1 - player.y]) / self.POS_STD

    def _rays(self, player: PlayerData, segments: np.ndarray) -> np.ndarray:
        dist = math.raycast((player.x, player.y), self._ray_dirs, segments, self.ray_range)
        return np.clip(1.0 - dist / self.ray_range, 0.0, 1.0)

    def _ground_probes(self, player: PlayerData) -> np.ndarray:
        """
        How close the nearest floor (hard or soft) is below each probe point.
        """
        origins = self._probe_offsets + [player.x, player.y]
        dist = math.raycast(origins, self._probe_dirs, self._floors, self.ray_range)
        return np.clip(1.0 - dist / self.ray_range, 0.0, 1.0)
