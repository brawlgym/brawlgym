from typing import Dict, Optional

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class TimeoutPenalty(RewardFunction):
    """
    -penalty when the clock runs out, to whoever did not win the exchange.

    A timeout nobody landed a hit in is a mutual stall, and charges everyone.

    max_steps must match the TimeoutCondition the match is using.
    """

    def __init__(self, max_steps: int, penalty: float = 1.0,
                 decide_on_damage: bool = True, win_bonus: float = 0.0):
        self.max_steps = int(max_steps)
        self.penalty = float(penalty)
        self.decide_on_damage = bool(decide_on_damage)
        self.win_bonus = float(win_bonus)
        self._steps = 0
        self._dealt_at_reset: Dict[int, float] = {}
        self._cache_state: Optional[GameState] = None
        self._cache: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._steps = 0
        self._dealt_at_reset = {p.port: p.damage_dealt for p in initial_state.players}
        self._cache_state = None
        self._cache = {}

    def _episode_damage(self, player: PlayerData) -> float:
        return max(0.0, player.damage_dealt - self._dealt_at_reset.get(player.port, player.damage_dealt))

    def _compute(self, state: GameState) -> Dict[int, float]:
        if not self.decide_on_damage:
            return {p.port: -self.penalty for p in state.players}
        dealt = {p.port: self._episode_damage(p) for p in state.players}
        best = max(dealt.values()) if dealt else 0.0
        if best <= 0.0:
            return {port: -self.penalty for port in dealt}
        return {port: (self.win_bonus if d >= best else -self.penalty) for port, d in dealt.items()}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        # called once per fighter per step; count the step, not the call
        if state is not self._cache_state:
            self._cache_state = state
            self._steps += 1
            self._cache = self._compute(state) if self._steps >= self.max_steps else {}
        return self._cache.get(player.port, 0.0)
