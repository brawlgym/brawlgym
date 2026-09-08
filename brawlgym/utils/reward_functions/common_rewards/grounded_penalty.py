from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class GroundedPenalty(RewardFunction):
    """
    -1 each step the agent is standing on the ground. Meant to be tiny: a nudge away from camping
    the floor, not a reason to jump.
    """

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        return -1.0 if player.on_ground else 0.0
