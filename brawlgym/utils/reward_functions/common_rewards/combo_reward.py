from typing import Dict, Optional

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class ComboReward(RewardFunction):
    """
    Rewards follow-up hits: a hit landed on an opponent who was in hitstun at most max_gap steps
    earlier. The reward scales with how tight the follow-up was, link_reward for a hit that lands
    while the opponent is still stunned (a true combo) down to a fraction of it at max_gap steps
    after their hitstun ended.
    """

    def __init__(self, link_reward: float = 1.0, max_gap: int = 15):
        self.link_reward = link_reward
        self.max_gap = int(max_gap)
        self._since_stun: Dict[int, Optional[int]] = {}   # steps since the fighter was last stunned
        self._dealt: Dict[int, float] = {}
        self._cache_state: Optional[GameState] = None
        self._cache: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._since_stun = {p.port: (0 if p.stunned else None) for p in initial_state.players}
        self._dealt = {p.port: p.damage_dealt for p in initial_state.players}
        self._cache_state = None

    def _link_value(self, victim: PlayerData) -> float:
        gap = self._since_stun.get(victim.port)
        if victim.hits_taken <= 0 or gap is None or gap > self.max_gap:
            return 0.0
        return self.link_reward * victim.hits_taken * (1.0 - gap / (self.max_gap + 1.0))

    def _compute(self, state: GameState) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for team, members in state.teams().items():
            links = sum(self._link_value(p) for p in state.players if p.team != team)
            hitters = [p for p in members if p.damage_dealt > self._dealt.get(p.port, p.damage_dealt)]
            for p in members:
                out[p.port] = links / len(hitters) if p in hitters else 0.0
        for p in state.players:
            prev = self._since_stun.get(p.port)
            self._since_stun[p.port] = 0 if p.stunned else (None if prev is None else prev + 1)
            self._dealt[p.port] = p.damage_dealt
        return out

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        if state is not self._cache_state:
            self._cache = self._compute(state)
            self._cache_state = state
        return self._cache.get(player.port, 0.0)
