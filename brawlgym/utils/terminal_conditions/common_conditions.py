"""
Terminal conditions: decide when an episode ends.
"""
from __future__ import annotations

from ..gamestates import GameState


from .terminal_condition import TerminalCondition


class TeamWipeCondition(TerminalCondition):
    """
    Episode ends when every player on any one team is dead.

    Dead players sit out (visibly held by their sidekick) instead of respawning, so a wipe
    is stable: the match itself keeps running and reset() revives everyone.
    """

    def is_terminal(self, current_state: GameState) -> bool:
        teams = current_state.teams()
        if len(teams) < 2:
            return False
        return any(all(p.dead for p in members) for members in teams.values())


class TimeoutCondition(TerminalCondition):
    """
    Episode ends after max_steps env steps.
    """

    def __init__(self, max_steps: int):
        self.max_steps = max_steps
        self._steps = 0

    def reset(self, initial_state: GameState) -> None:
        self._steps = 0

    def is_terminal(self, current_state: GameState) -> bool:
        self._steps += 1
        return self._steps >= self.max_steps
