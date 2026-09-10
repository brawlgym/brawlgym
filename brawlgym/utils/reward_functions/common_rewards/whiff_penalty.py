from typing import Dict

from ...gamestates import GameState, PlayerData
from ..attack_history import AttackHistory
from ..reward_function import RewardFunction


class WhiffPenalty(RewardFunction):
    """
    -penalty every time one of the agent's attacks ends without having dealt any damage.

    Uses the fighter's attacking flag, so no timing assumptions: an attack is a whiff exactly when
    the flag drops and damage_dealt has not moved since it rose.

    heavy_without_light_scale multiplies the penalty for a heavy that no light set up inside the
    window; it defaults to 1.0, which penalizes every whiff the same.
    """

    def __init__(self, penalty: float = 1.0,
                 heavy_without_light_scale: float = 1.0,
                 light_window_seconds: float = 2.0):
        self.penalty = penalty
        self.heavy_without_light_scale = float(heavy_without_light_scale)
        self._attacks = AttackHistory(light_window_seconds)
        self._attacking: Dict[int, bool] = {}
        self._dealt_at_start: Dict[int, float] = {}

    def set_tick_skip(self, tick_skip: int) -> None:
        self._attacks.set_tick_skip(tick_skip)

    def reset(self, initial_state: GameState) -> None:
        self._attacking = {p.port: p.attacking for p in initial_state.players}
        self._dealt_at_start = {p.port: p.damage_dealt for p in initial_state.players}
        self._attacks.reset(initial_state)

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        self._attacks.update(player, previous_action)
        was = self._attacking.get(player.port, False)
        r = 0.0
        if player.attacking and not was:
            self._dealt_at_start[player.port] = player.damage_dealt
        elif was and not player.attacking:
            if player.damage_dealt <= self._dealt_at_start.get(player.port, player.damage_dealt):
                r = -self.penalty
                if self._attacks.is_heavy_without_light(player.port):
                    r *= self.heavy_without_light_scale
        self._attacking[player.port] = player.attacking
        return r
