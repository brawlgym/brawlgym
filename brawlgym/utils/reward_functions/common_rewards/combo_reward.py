from typing import Dict, Optional

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class ComboReward(RewardFunction):
    """
    +link_reward for every hit the agent lands on an opponent who was in hitstun at most max_gap
    steps earlier, i.e. a follow-up that came before the opponent had much chance to act.

    max_gap is measured in env steps. Stack several with decreasing rewards for a tighter-is-better
    scale; a hit that qualifies for a strict one qualifies for every looser one as well.
    """

    def __init__(self, link_reward: float = 1.0, max_gap: int = 5):
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

    def _is_link(self, victim: PlayerData) -> bool:
        gap = self._since_stun.get(victim.port)
        return victim.hits_taken > 0 and gap is not None and gap <= self.max_gap

    def _compute(self, state: GameState) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for team, members in state.teams().items():
            links = sum(p.hits_taken for p in state.players if p.team != team and self._is_link(p))
            hitters = [p for p in members if p.damage_dealt > self._dealt.get(p.port, p.damage_dealt)]
            for p in members:
                out[p.port] = self.link_reward * links / len(hitters) if p in hitters else 0.0
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


class TrueComboReward(ComboReward):
    """
    +link_reward for every hit landed while the opponent was still in hitstun: a link they could
    not have acted out of.
    """

    def __init__(self, link_reward: float = 1.0):
        super().__init__(link_reward, max_gap=0)
