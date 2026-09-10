from typing import Dict

from ...gamestates import GameState, PlayerData
from ..attack_history import AttackHistory
from ..reward_function import RewardFunction


class DamageDealtReward(RewardFunction):
    """
    +1 per point of damage the agent dealt this step.

    Read from the game's per-fighter running total, so it is credited to the fighter who landed the
    hit and ignores friendly fire.

    The scales grade the attack that dealt it, and both default to 1.0 (plain damage):
    repeat_move_scale applies when the swing is the same move as the one before it, and
    heavy_without_light_scale when a heavy goes out with no light thrown inside the window.
    """

    def __init__(self, repeat_move_scale: float = 1.0,
                 heavy_without_light_scale: float = 1.0,
                 light_window_seconds: float = 2.0):
        self.repeat_move_scale = float(repeat_move_scale)
        self.heavy_without_light_scale = float(heavy_without_light_scale)
        self._attacks = AttackHistory(light_window_seconds)
        self._prev: Dict[int, float] = {}

    def set_tick_skip(self, tick_skip: int) -> None:
        self._attacks.set_tick_skip(tick_skip)

    def reset(self, initial_state: GameState) -> None:
        self._prev = {p.port: p.damage_dealt for p in initial_state.players}
        self._attacks.reset(initial_state)

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        self._attacks.update(player, previous_action)
        dealt = max(0.0, player.damage_dealt - self._prev.get(player.port, player.damage_dealt))
        self._prev[player.port] = player.damage_dealt
        if dealt <= 0.0:
            return 0.0
        scale = 1.0
        if self._attacks.is_repeat(player.port):
            scale *= self.repeat_move_scale
        if self._attacks.is_heavy_without_light(player.port):
            scale *= self.heavy_without_light_scale
        return dealt * scale
