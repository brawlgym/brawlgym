from typing import Dict

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class DamageDealtReward(RewardFunction):
    """
    +1 per point of damage the agent dealt this step.

    Read from the game's per-fighter running total, so it is credited to the fighter who landed the
    hit and ignores friendly fire.
    """

    def __init__(self):
        self._prev: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._prev = {p.port: p.damage_dealt for p in initial_state.players}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        dealt = max(0.0, player.damage_dealt - self._prev.get(player.port, player.damage_dealt))
        self._prev[player.port] = player.damage_dealt
        return dealt
