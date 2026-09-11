"""
Attack bookkeeping for the rewards that grade a swing instead of just counting it.
"""
from typing import Any, Dict, Optional, Tuple

from ..common_values import BUTTON_NAMES, NATIVE_FPS
from ..gamestates import GameState, PlayerData

_UP = BUTTON_NAMES.index("up")
_DOWN = BUTTON_NAMES.index("down")
_LEFT = BUTTON_NAMES.index("left")
_RIGHT = BUTTON_NAMES.index("right")
_LIGHT = BUTTON_NAMES.index("light")
_HEAVY = BUTTON_NAMES.index("heavy")

# how stale the last attack input may be and still be what started the animation
_INPUT_GRACE_STEPS = 2

Move = Tuple[str, str]


def attack_move(buttons: Any) -> Optional[Move]:
    """
    (direction, "light"|"heavy") for an input that swings, or None for one that does not.

    Left and right are one direction: a side attack is the same move mirrored, so turning around
    between swings is still the same swing.
    """
    if buttons is None:
        return None
    if buttons[_LIGHT]:
        strength = "light"
    elif buttons[_HEAVY]:
        strength = "heavy"
    else:
        return None
    if buttons[_UP]:
        direction = "up"
    elif buttons[_DOWN]:
        direction = "down"
    elif buttons[_LEFT] or buttons[_RIGHT]:
        direction = "side"
    else:
        direction = "neutral"
    return direction, strength


class AttackHistory:
    """
    What a fighter is swinging, and what it swung before.

    Each attack is graded once, when the fighter's attacking flag rises, from the input that
    started it. The grade then stands until the next attack begins, so damage that lands a few
    steps after the input is still attributed to the swing that caused it.

    Own one per reward function rather than sharing: they are fed the same state and the same
    action every step, so two copies stay in lockstep without any coupling between them.
    """

    def __init__(self, light_window_seconds: float = 2.0, tick_skip: int = 4):
        self.light_window_seconds = float(light_window_seconds)
        self.set_tick_skip(tick_skip)
        self._attacking: Dict[int, bool] = {}
        self._since_light: Dict[int, int] = {}
        self._pending: Dict[int, Move] = {}
        self._pending_age: Dict[int, int] = {}
        self._last_move: Dict[int, Optional[Move]] = {}
        self._repeat: Dict[int, bool] = {}
        self._cold_heavy: Dict[int, bool] = {}
        self._named: Dict[int, bool] = {}

    def set_tick_skip(self, tick_skip: int) -> None:
        steps_per_second = NATIVE_FPS / max(1, int(tick_skip))
        self._light_window_steps = int(round(self.light_window_seconds * steps_per_second))

    def reset(self, initial_state: GameState) -> None:
        ports = [p.port for p in initial_state.players]
        self._attacking = {p.port: p.attacking for p in initial_state.players}
        # nobody has thrown a light yet, so a heavy off the reset counts as unset up
        self._since_light = {port: self._light_window_steps + 1 for port in ports}
        self._pending = {}
        self._pending_age = {}
        self._last_move = {port: None for port in ports}
        self._repeat = {port: False for port in ports}
        self._cold_heavy = {port: False for port in ports}
        self._named = {port: False for port in ports}

    def update(self, player: PlayerData, previous_action: Any) -> None:
        """
        Take one step of inputs for one fighter. Call once per step, before reading the grades.
        """
        port = player.port
        buttons = previous_action
        move = attack_move(buttons)

        if buttons is not None and buttons[_LIGHT]:
            self._since_light[port] = 0
        else:
            self._since_light[port] = self._since_light.get(port, self._light_window_steps + 1) + 1

        if move is not None:
            self._pending[port] = move
            self._pending_age[port] = 0
        else:
            self._pending_age[port] = self._pending_age.get(port, _INPUT_GRACE_STEPS + 1) + 1

        was = self._attacking.get(port, False)
        if player.attacking and not was:
            self._grade(port)
        self._attacking[port] = player.attacking

    def _grade(self, port: int) -> None:
        """
        Score the attack that just started against the one before it.
        """
        fresh = self._pending_age.get(port, _INPUT_GRACE_STEPS + 1) <= _INPUT_GRACE_STEPS
        move = self._pending.get(port) if fresh else None
        if move is None:
            self._named[port] = False
            self._repeat[port] = False
            self._cold_heavy[port] = False
            return
        self._named[port] = True
        self._repeat[port] = move == self._last_move.get(port)
        self._cold_heavy[port] = (move[1] == "heavy"
                                  and self._since_light.get(port, 0) > self._light_window_steps)
        self._last_move[port] = move

    def is_repeat(self, port: int) -> bool:
        """
        True when the current attack is the same move as the one before it.
        """
        return self._repeat.get(port, False)

    def is_heavy_without_light(self, port: int) -> bool:
        """
        True when the current attack is a heavy that no light set up inside the window.
        """
        return self._cold_heavy.get(port, False)

    def is_named_attack(self, port: int) -> bool:
        """
        True when the current attack was started by a light or heavy input.
        """
        return self._named.get(port, False)
