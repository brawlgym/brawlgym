"""
Drives a live Brawlhalla instance in deterministic lockstep: every `step()` advances the
simulation exactly `tick_skip` frames with inputs applied, then returns the resulting
state.

Requires the `brawlgym_core` engine module and a running, injected game instance.
"""
from __future__ import annotations

import time
from typing import Any, List, Optional, Sequence

from ..utils.action_parsers import ActionParser, DefaultAction, mask_to_buttons
from ..utils.common_values import DEFAULT_MAP, NATIVE_FPS, UNCAPPED_RENDER_FPS
from ..utils.gamestates import GameState
from ..utils.obs_builders import DefaultObs, ObsBuilder
from ..utils.reward_functions import CombinedReward, DamageDealtReward, KOReward, RewardFunction
from ..utils.state_setters import DefaultStateSetter, StateSetter
from ..utils.terminal_conditions import TeamWipeCondition, TerminalCondition, TimeoutCondition

try:
    from ..core import brawlgym_core      # engine bridge, shipped inside the package
except ImportError:                       # pragma: no cover
    try:
        import brawlgym_core              # dev: built alongside, found on sys.path
    except ImportError as _e:
        brawlgym_core = None
        _core_import_error = _e


class Match:
    """
    Gym style match over a live game instance.
    """

    def __init__(self,
                 game_speed: float = 0,  # 0: uncapped, 1: real time, >1: multiple of real time
                 tick_skip: int = 8,
                 n_players: int = 2,
                 map_name: Optional[str] = None,
                 legends: Optional[Sequence[Any]] = None,
                 terminal_conditions: Optional[Sequence[TerminalCondition]] = None,
                 reward_function: Optional[RewardFunction] = None,
                 obs_builder: Optional[ObsBuilder] = None,
                 action_parser: Optional[ActionParser] = None,
                 state_setter: Optional[StateSetter] = None,
                 auto_minimize: bool = False,
                 auto_mute: bool = False,
                 host: str = "127.0.0.1",
                 port: int = 8790):
        if brawlgym_core is None:
            raise ImportError(
                "brawlgym requires the brawlgym_core engine module; install it and ensure it is importable") from _core_import_error
        if game_speed < 0:
            raise ValueError("game_speed must be 0 (uncapped) or a positive multiple of real time")
        self.game_speed = float(game_speed)
        self.tick_skip = int(tick_skip)
        self.n_players = int(n_players)
        # A match cannot start without a locked map
        # map_name=None uses small brawlhaven
        self.map_name = map_name or DEFAULT_MAP
        # per-slot legends (HeroIDs or names)
        # team 1: 0,2,4,6
        # team 2: 1,3,5,7
        # None = the engine's default roster.
        self.legends: Optional[List[int]] = self._resolve_legends(legends) if legends else None
        self.terminal_conditions: List[TerminalCondition] = list(
            terminal_conditions if terminal_conditions is not None
            else [TeamWipeCondition(), TimeoutCondition(1200)])
        self.reward_function = reward_function or CombinedReward(
            [DamageDealtReward(), KOReward(ko_reward=200.0, death_penalty=200.0)])
        self.obs_builder = obs_builder or DefaultObs()
        self.action_parser = action_parser or DefaultAction()
        self.state_setter = state_setter or DefaultStateSetter()
        self.auto_minimize = bool(auto_minimize)
        self.auto_mute = bool(auto_mute)
        self.map_info = brawlgym_core.get_map_geometry(self.map_name)
        for comp in (self.obs_builder, self.state_setter):
            if hasattr(comp, "set_map_info"):
                comp.set_map_info(self.map_info)
        # NOTE: the engine's internal `framems` stays at 25ms regardless of speed - it is the
        # forced-step owed-time, chosen so exactly ONE 60fps frame runs per step (floor math
        # needs it in [16.7, 33.3)); it does not affect game speed.

        # wall-clock period of one step for a capped speed; 0 = step as fast as the game answers
        self._step_period = self.tick_skip / NATIVE_FPS / self.game_speed if self.game_speed else 0.0
        self._next_step_time: Optional[float] = None

        self._bridge = brawlgym_core.HookBridge(host, port)
        self._state: Optional[GameState] = None
        self._prev_actions: Optional[Sequence[Any]] = None

    @staticmethod
    def _resolve_legends(legends: Sequence[Any]) -> List[int]:
        """
        Resolve a mixed list of HeroIDs and legend names to HeroIDs.
        """
        ids: List[int] = []
        table = None
        for item in legends:
            if isinstance(item, str):
                if table is None:
                    if not hasattr(brawlgym_core, "list_legends"):
                        raise ValueError("cannot resolve legend names pass numeric HeroIDs instead")
                    table = {}
                    for hid, hero_name, bio_name in brawlgym_core.list_legends():
                        table[str(hero_name).lower()] = int(hid)
                        if bio_name:
                            table[str(bio_name).lower()] = int(hid)
                key = item.lower()
                if key not in table:
                    raise ValueError("unknown legend %r" % item)
                ids.append(table[key])
            else:
                ids.append(int(item))
        return ids

    def connect(self, timeout: float = 300.0) -> GameState:
        """
        Wait for the game, then for a running match; enable sit-out-on-death.

        The game must be launched and a match started. Returns the first observed state.
        """
        print("[brawlgym] waiting for the game ...", flush=True)
        self._bridge.wait_for_hook(timeout)
        # roster size + legends for the auto-started match specified before the party forms
        self._bridge.set_player_count(self.n_players)
        if self.legends:
            self._bridge.set_legends(self.legends)
        st = self._wait_for_match(timeout)
        self._bridge.configure(max(16, self.tick_skip * 2), 25.0)
        self._bridge.set_render_fps(UNCAPPED_RENDER_FPS if self.game_speed == 0 else NATIVE_FPS)
        self._bridge.set_sitout(True)           # deaths sit out until reset()
        self._state = st
        speed = "uncapped" if self.game_speed == 0 else "%gx" % self.game_speed
        print("[brawlgym] match up: %d fighters, game speed %s" % (len(st.players), speed), flush=True)
        from ..gamelaunch import window         # matches by window title / process name (single instance)
        if self.auto_minimize:
            window.minimize_title("Brawlhalla")
        if window.pycaw_available():
            window.mute_name("Brawlhalla.exe", mute=self.auto_mute)
        elif self.auto_mute:
            print("[brawlgym] pycaw not installed - cannot mute (pip install pycaw)")
        return st

    def _wait_for_match(self, timeout: float) -> GameState:
        """
        Poll until fighters exist.
        """
        t_end = time.time() + timeout
        while time.time() < t_end:
            try:
                st = GameState(self._bridge.get_state())
                players = st.players
                if len(players) >= 2 and all(p.x > -5000 for p in players):
                    return st
            except Exception:
                try:
                    self._bridge.wait_for_hook(30)
                except Exception:
                    pass
            time.sleep(1.0)
        raise TimeoutError("no running match detected - start a match in the game")

    def close(self) -> None:
        self._bridge.close()

    @property
    def n_agents(self) -> int:
        return len(self._state.players) if self._state else 0

    def reset(self) -> List[Any]:
        """
        Revive + reposition every fighter, reset all components, return initial obs.
        """
        if self._state is None:
            self.connect()
        n = len(self._state.players)
        positions = [(int(round(x)), int(round(y)))
                     for x, y in self.state_setter.build_positions(n)]
        st = GameState(self._bridge.reset(positions))
        self._state = st
        self._prev_actions = None
        self._next_step_time = None
        self.obs_builder.reset(st)
        self.reward_function.reset(st)
        for tc in self.terminal_conditions:
            tc.reset(st)
        # no buttons pressed yet
        no_buttons = mask_to_buttons(0)
        return [self.obs_builder.build_obs(p, st, no_buttons) for p in st.players]

    def _pace(self) -> None:
        """
        Hold the step schedule for a capped game_speed.
        """
        if not self._step_period:
            return
        now = time.perf_counter()
        # (re)anchor the schedule at the first step and after any stall longer than a step
        if self._next_step_time is None or now - self._next_step_time > self._step_period:
            self._next_step_time = now
        self._next_step_time += self._step_period
        delay = self._next_step_time - now
        if delay > 0:
            time.sleep(delay)

    def step(self, actions: Sequence[Any]):
        """
        Advance tick_skip frames with the given per-agent actions.

        Returns (observations, rewards, terminated, game_state). Obs builders and reward
        functions receive each fighter's previous action as the buttons that were pressed
        (one 0/1 per BUTTON_BITS entry), whatever the action parser's own format.
        """
        self._pace()
        masks = self.action_parser.parse_actions(actions, self._state)
        st = GameState(self._bridge.step(masks, self.tick_skip))
        self._state = st
        self._prev_actions = actions
        buttons = [mask_to_buttons(m) for m in masks]
        obs = [self.obs_builder.build_obs(p, st, b) for p, b in zip(st.players, buttons)]
        rewards = [self.reward_function.get_reward(p, st, b)
                   for p, b in zip(st.players, buttons)]
        terminated = any(tc.is_terminal(st) for tc in self.terminal_conditions)
        return obs, rewards, terminated, st
