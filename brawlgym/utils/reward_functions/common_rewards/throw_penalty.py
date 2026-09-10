from typing import Dict

from ...common_values import BUTTON_NAMES, NATIVE_FPS
from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction

_THROW = BUTTON_NAMES.index("throw")


class ThrowPenalty(RewardFunction):
    """
    -penalty when the agent throws away the weapon it was holding.

    A weapon leaves a fighter's hands for reasons that are not its choice - a hard enough hit
    disarms it, a KO drops everything - so this only fires when the fighter pressed throw just
    before losing it, inside input_window_seconds.

    Gadgets are ignored: throwing a bomb is what a bomb is for.
    """

    def __init__(self, penalty: float = 1.0, input_window_seconds: float = 0.5):
        self.penalty = float(penalty)
        self.input_window_seconds = float(input_window_seconds)
        self.set_tick_skip(4)
        self._had_weapon: Dict[int, bool] = {}
        self._since_throw: Dict[int, int] = {}

    def set_tick_skip(self, tick_skip: int) -> None:
        steps_per_second = NATIVE_FPS / max(1, int(tick_skip))
        self._window_steps = int(round(self.input_window_seconds * steps_per_second))

    def reset(self, initial_state: GameState) -> None:
        self._had_weapon = {p.port: p.has_weapon for p in initial_state.players}
        self._since_throw = {p.port: self._window_steps + 1 for p in initial_state.players}

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        port = player.port
        stale = self._window_steps + 1
        if previous_action is not None and previous_action[_THROW]:
            self._since_throw[port] = 0
        else:
            self._since_throw[port] = self._since_throw.get(port, stale) + 1

        had = self._had_weapon.get(port, player.has_weapon)
        self._had_weapon[port] = player.has_weapon
        if had and not player.has_weapon and not player.dead \
                and self._since_throw.get(port, stale) <= self._window_steps:
            return -self.penalty
        return 0.0
