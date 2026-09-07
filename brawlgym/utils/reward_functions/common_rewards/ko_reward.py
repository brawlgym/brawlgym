from typing import Dict

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class KOReward(RewardFunction):
    """
    +ko_reward when an opponent dies; -death_penalty when the agent dies.
    """

    def __init__(self, ko_reward: float = 1.0, death_penalty: float = 1.0):
        self.ko_reward = ko_reward
        self.death_penalty = death_penalty
        self._dead: Dict[int, bool] = {}

    def reset(self, initial_state: GameState) -> None:
        self._dead = {p.port: p.dead for p in initial_state.players}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        r = 0.0
        for opp in state.opponents_of(player):
            if opp.dead and not self._dead.get(opp.port, False):
                r += self.ko_reward
        if player.dead and not self._dead.get(player.port, False):
            r -= self.death_penalty
        for p in state.players:
            self._dead[p.port] = p.dead
        return r
