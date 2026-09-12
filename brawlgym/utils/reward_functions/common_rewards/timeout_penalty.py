from typing import Optional

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class TimeoutPenalty(RewardFunction):
    """
    -penalty to every fighter on the step the episode runs out of time.

    max_steps must match the TimeoutCondition the match is using.
    """

    def __init__(self, max_steps: int, penalty: float = 1.0):
        self.max_steps = int(max_steps)
        self.penalty = float(penalty)
        self._steps = 0
        self._cache_state: Optional[GameState] = None

    def reset(self, initial_state: GameState) -> None:
        self._steps = 0
        self._cache_state = None

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        # called once per fighter per step; count the step, not the call
        if state is not self._cache_state:
            self._cache_state = state
            self._steps += 1
        return -self.penalty if self._steps >= self.max_steps else 0.0
