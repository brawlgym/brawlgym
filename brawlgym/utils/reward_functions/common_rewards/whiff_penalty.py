from typing import Dict

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class WhiffPenalty(RewardFunction):
    """
    -penalty every time one of the agent's attacks ends without having dealt any damage.

    Uses the fighter's attacking flag, so no timing assumptions: an attack is a whiff exactly when
    the flag drops and damage_dealt has not moved since it rose.
    """

    def __init__(self, penalty: float = 1.0):
        self.penalty = penalty
        self._attacking: Dict[int, bool] = {}
        self._dealt_at_start: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._attacking = {p.port: p.attacking for p in initial_state.players}
        self._dealt_at_start = {p.port: p.damage_dealt for p in initial_state.players}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        was = self._attacking.get(player.port, False)
        r = 0.0
        if player.attacking and not was:
            self._dealt_at_start[player.port] = player.damage_dealt
        elif was and not player.attacking:
            if player.damage_dealt <= self._dealt_at_start.get(player.port, player.damage_dealt):
                r = -self.penalty
        self._attacking[player.port] = player.attacking
        return r
