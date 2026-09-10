from typing import Dict, Optional

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
        self._cache_state: Optional[GameState] = None
        self._cache: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._dead = {p.port: p.dead for p in initial_state.players}
        self._cache_state = None

    def _compute(self, state: GameState) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for player in state.players:
            r = 0.0
            for opp in state.opponents_of(player):
                if opp.dead and not self._dead.get(opp.port, False):
                    r += self.ko_reward
            if player.dead and not self._dead.get(player.port, False):
                r -= self.death_penalty
            out[player.port] = r
        self._dead = {p.port: p.dead for p in state.players}
        return out

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        if state is not self._cache_state:
            self._cache = self._compute(state)
            self._cache_state = state
        return self._cache.get(player.port, 0.0)
