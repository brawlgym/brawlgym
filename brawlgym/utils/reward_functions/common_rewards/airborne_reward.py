from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class AirborneReward(RewardFunction):
    """
    +1 each step the agent is off the ground. Encourages jumping and fighting in the air.
    """

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        return 0.0 if player.on_ground else 1.0
