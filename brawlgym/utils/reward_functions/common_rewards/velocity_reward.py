import numpy as np

from ... import common_values
from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class VelocityReward(RewardFunction):
    """
    The agent's speed each step, normalized. Keeps the fighter moving.
    """

    def __init__(self, vel_std: float = common_values.VEL_STD):
        self.vel_std = vel_std

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        return float(np.hypot(player.vx, player.vy)) / self.vel_std
