from typing import Dict

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class DamageTakenPenalty(RewardFunction):
    """
    -1 per point of damage the agent took from an opponent this step.

    Read from the game's running total, which keeps counting across deaths where damage resets.
    """

    def __init__(self, counterhit_scale: float = 1.0):
        self.counterhit_scale = float(counterhit_scale)
        self._prev: Dict[int, float] = {}
        self._attacking: Dict[int, bool] = {}

    def reset(self, initial_state: GameState) -> None:
        self._prev = {p.port: p.damage_taken for p in initial_state.players}
        self._attacking = {p.port: p.attacking for p in initial_state.players}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        taken = max(0.0, player.damage_taken - self._prev.get(player.port, player.damage_taken))
        self._prev[player.port] = player.damage_taken
        was = self._attacking.get(player.port, False)
        self._attacking[player.port] = player.attacking
        if taken <= 0.0:
            return 0.0
        if was or player.attacking:
            taken *= self.counterhit_scale
        return -taken
