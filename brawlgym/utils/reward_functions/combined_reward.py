from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from ..gamestates import GameState, PlayerData
from .reward_function import RewardFunction


class CombinedReward(RewardFunction):
    """
    A reward composed of multiple rewards.
    """

    def __init__(self, reward_functions: Sequence[RewardFunction],
                 reward_weights: Optional[Sequence[float]] = None):
        """
        :param reward_functions: Each individual reward function.
        :param reward_weights: The weights for each reward.
        """
        super().__init__()
        self.reward_functions = tuple(reward_functions)
        self.reward_weights = tuple(reward_weights) if reward_weights is not None \
            else tuple(1.0 for _ in self.reward_functions)

        if len(self.reward_functions) != len(self.reward_weights):
            raise ValueError("Reward functions list length ({0}) and reward weights length ({1}) must be equal"
                             .format(len(self.reward_functions), len(self.reward_weights)))
        # unweighted per-component rewards from the latest get_reward call by player port
        self.last_rewards: Dict[int, List[float]] = {}

    @classmethod
    def from_zipped(cls, *rewards_and_weights: Union[RewardFunction, Tuple[RewardFunction, float]]) -> "CombinedReward":
        """
        Alternate constructor which takes any number of either rewards, or (reward, weight) tuples.
        """
        rewards = []
        weights = []
        for value in rewards_and_weights:
            if isinstance(value, tuple):
                r, w = value
            else:
                r, w = value, 1.0
            rewards.append(r)
            weights.append(w)
        return cls(tuple(rewards), tuple(weights))

    def reset(self, initial_state: GameState) -> None:
        for func in self.reward_functions:
            func.reset(initial_state)

    def set_tick_skip(self, tick_skip: int) -> None:
        for func in self.reward_functions:
            func.set_tick_skip(tick_skip)

    def get_reward(self, player: PlayerData, state: GameState, previous_action: np.ndarray) -> float:
        rewards = [func.get_reward(player, state, previous_action) for func in self.reward_functions]
        self.last_rewards[player.port] = rewards
        return float(np.dot(self.reward_weights, rewards))
