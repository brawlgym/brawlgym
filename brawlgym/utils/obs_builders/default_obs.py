import numpy as np
from collections import deque
from typing import Any, Dict, List

from .. import common_values, math
from ..legends import LEGEND_IDS, LEGEND_INDEX
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
    distance to the edge of the platform underfoot is read directly. Loose items get a fixed
    number of slots, nearest first, sized from the game's spawn cap for the roster. Each 
    fighter block ends with which wall it is on and how much stamina it has spent.

    Layout: [recent actions, blast-edge distances, rays (hard), rays (soft), ground probes,
             self, teammates (port order), opponents (port order), items (nearest first)].
    """

    GROUND_PROBE_OFFSETS = (-1000.0, -500.0, -250.0, -100.0, 100.0, 250.0, 500.0, 1000.0)

    LEGEND_IDS = LEGEND_IDS
    ITEM_TYPES = common_values.ITEM_TYPES
    HELD_TYPES = common_values.WEAPONS + common_values.GADGETS
    ITEM_FEATURES = 5 + len(ITEM_TYPES)

    def __init__(self, 
                 n_rays: int = 16, 
                 ray_range: float = 2000.0, 
                 n_item_slots: int = None,
                 legend_one_hot: bool = True,
                 n_action_history: int = 4,
                 pos_std: float = common_values.POS_STD,
                 vel_std: float = common_values.VEL_STD,
                 damage_std: float = common_values.DAMAGE_STD):
        """
        :param n_rays: Rays cast around the fighter to sense the stage.
        :param ray_range: Distance in px beyond which a ray reports nothing.
        :param n_item_slots: Loose items observed, nearest first. None = the game's spawn cap for the
                             roster size (common_values.max_items_on_stage), fixed at the first reset.
        :param legend_one_hot: Include which legend each fighter is, one-hot over every playable one.
        :param pos_std: Position normalization coefficient for relative positions.
        :param vel_std: Velocity normalization coefficient.
        :param damage_std: Damage normalization coefficient.
        """
        super().__init__()
        self.n_rays = n_rays
        self.ray_range = float(ray_range)
        self.n_item_slots = n_item_slots
        self.legend_one_hot = legend_one_hot
        self.n_action_history = max(1, int(n_action_history))
        self._actions: Dict[int, deque] = {}
        self._stamina_state = None
        self._stamina_base: Dict[int, int] = {}
        self._stamina_used: Dict[int, int] = {}
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
        if self.n_item_slots is None:
            self.n_item_slots = common_values.max_items_on_stage(len(initial_state.players))
        self._actions = {p.port: self._blank_history() for p in initial_state.players}
        self._stamina_state = None
        self._stamina_base = {p.port: p.jumps_used for p in initial_state.players}
        self._stamina_used = {p.port: 0 for p in initial_state.players}

    def _update_stamina(self, state: GameState) -> None:
        """
        Stamina: aerial jumps/recoveries spent since the fighter last touched the ground OR a wall.
        """
        if state is self._stamina_state:
            return
        self._stamina_state = state
        for p in state.players:
            if p.on_ground or p.on_wall:
                self._stamina_base[p.port] = p.jumps_used
            base = self._stamina_base.setdefault(p.port, p.jumps_used)
            self._stamina_used[p.port] = max(0, p.jumps_used - base)

    def _blank_history(self) -> deque:
        return deque([np.zeros(common_values.NUM_BUTTONS)] * self.n_action_history,
                     maxlen=self.n_action_history)

    def _recent_actions(self, player: PlayerData, previous_action) -> np.ndarray:
        """
        The buttons from the last n_action_history decisions for this fighter, oldest first.
        """
        history = self._actions.get(player.port)
        if history is None:
            history = self._actions.setdefault(player.port, self._blank_history())
        history.append(np.asarray(previous_action, dtype=np.float32).reshape(-1))
        return np.concatenate(history)

    def build_obs(self, player: PlayerData, state: GameState, previous_action: np.ndarray) -> Any:
        self._update_stamina(state)
        obs = [self._recent_actions(player, previous_action),
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
        obs.append(self._items(player, state))
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
             self._stamina_used.get(player.port, 0) / common_values.MAX_JUMPS,
             int(player.has_weapon),
             int(player.dead)],
            self._one_hot(player.held_item, self.HELD_TYPES),
            self._wall(player)])
        if self.legend_one_hot:
            legend = np.zeros(len(self.LEGEND_IDS))
            idx = LEGEND_INDEX.get(player.hero_id)
            if idx is not None:
                legend[idx] = 1.0
            obs.append(legend)

    @staticmethod
    def _wall(player: PlayerData) -> np.ndarray:
        """
        Which wall the fighter is on, if any. 0 = none, 1 = right wall, 2 = left wall.
        """
        out = np.zeros(3) 
        side = player.wall_side
        if 0 <= side < 3:
            out[side] = 1.0
        return out

    @staticmethod
    def _one_hot(name: str, names) -> np.ndarray:
        out = np.zeros(len(names))
        if name in names:
            out[names.index(name)] = 1.0
        return out

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

    def _items(self, player: PlayerData, state: GameState) -> np.ndarray:
        """
        The nearest loose items, one slot each: [present, one-hot type, dx, dy, vx, vy]. Empty
        slots are zeros.
        """
        if self.n_item_slots is None:
            self.n_item_slots = common_values.max_items_on_stage(len(state.players))
        out = np.zeros(self.n_item_slots * self.ITEM_FEATURES)
        nearest = sorted(state.items, key=lambda it: (it.x - player.x) ** 2 + (it.y - player.y) ** 2)
        for i, it in enumerate(nearest[:self.n_item_slots]):
            out[i * self.ITEM_FEATURES:(i + 1) * self.ITEM_FEATURES] = np.concatenate([
                [1.0], self._one_hot(it.name, self.ITEM_TYPES),
                [(it.x - player.x) / self.POS_STD, (it.y - player.y) / self.POS_STD,
                 it.vx / self.VEL_STD, it.vy / self.VEL_STD]])
        return out

    def _ground_probes(self, player: PlayerData) -> np.ndarray:
        """
        How close the nearest floor (hard or soft) is below each probe point.
        """
        origins = self._probe_offsets + [player.x, player.y]
        dist = math.raycast(origins, self._probe_dirs, self._floors, self.ray_range)
        return np.clip(1.0 - dist / self.ray_range, 0.0, 1.0)
