"""
Reward functions. Each gets the live GameState every step, per agent.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from ..gamestates import GameState, PlayerData


from .reward_function import RewardFunction


class ConstantReward(RewardFunction):
    """
    A constant per-step reward (e.g. a small negative time penalty).
    """

    def __init__(self, value: float = 0.0):
        self.value = value

    def get_reward(self, player, state, previous_action) -> float:
        return self.value


class DamageDealtReward(RewardFunction):
    """
    +1 per point of damage the agent's OPPONENTS accumulated this step.
    """

    def __init__(self):
        self._prev: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._prev = {p.port: p.damage for p in initial_state.players}

    def get_reward(self, player, state, previous_action) -> float:
        r = 0.0
        for opp in state.opponents_of(player):
            r += max(0.0, opp.damage - self._prev.get(opp.port, opp.damage))
        for p in state.players:
            self._prev[p.port] = p.damage
        return r


class DamageTakenPenalty(RewardFunction):
    """
    -1 per point of damage the agent itself accumulated this step.
    """

    def __init__(self):
        self._prev: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._prev = {p.port: p.damage for p in initial_state.players}

    def get_reward(self, player, state, previous_action) -> float:
        taken = max(0.0, player.damage - self._prev.get(player.port, player.damage))
        self._prev[player.port] = player.damage
        return -taken


class KOReward(RewardFunction):
    """
    +ko_reward when an opponent dies; -death_penalty when the agent dies.
    """

    def __init__(self, ko_reward: float = 1.0, death_penalty: float = 1.0):
        self.ko_reward = ko_reward
        self.death_penalty = death_penalty
        self._dead: Dict[int, bool] = {}

    def reset(self, initial_state: GameState) -> None:
        self._dead = {p.port: p.dead for p in initial_state.players}

    def get_reward(self, player, state, previous_action) -> float:
        r = 0.0
        for opp in state.opponents_of(player):
            if opp.dead and not self._dead.get(opp.port, False):
                r += self.ko_reward
        if player.dead and not self._dead.get(player.port, False):
            r -= self.death_penalty
        for p in state.players:
            self._dead[p.port] = p.dead
        return r


class CombinedReward(RewardFunction):
    """
    Weighted sum of several reward functions.
    """

    def __init__(self, reward_functions: Sequence[RewardFunction],
                 weights: Optional[Sequence[float]] = None):
        self.reward_functions: List[RewardFunction] = list(reward_functions)
        self.weights: List[float] = list(weights) if weights is not None \
            else [1.0] * len(self.reward_functions)
        if len(self.weights) != len(self.reward_functions):
            raise ValueError("weights must match reward_functions in length")

    def reset(self, initial_state: GameState) -> None:
        for fn in self.reward_functions:
            fn.reset(initial_state)

    def get_reward(self, player, state, previous_action) -> float:
        return sum(w * fn.get_reward(player, state, previous_action)
                   for fn, w in zip(self.reward_functions, self.weights))
