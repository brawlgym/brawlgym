from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class ConstantReward(RewardFunction):
    """
    A constant per-step reward (e.g. a small negative time penalty).
    """

    def __init__(self, value: float = 0.0):
        self.value = value

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        return self.value
