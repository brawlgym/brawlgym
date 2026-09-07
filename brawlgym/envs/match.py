"""
Drives a live Brawlhalla instance in deterministic lockstep: every `step()` advances the
simulation exactly `tick_skip` frames with inputs applied, then returns the resulting
state.

Requires the `brawlgym_core` engine module and a running, injected game instance.
"""
from __future__ import annotations

import time
from typing import Any, List, Optional, Sequence

from ..utils.action_parsers import ActionParser, DefaultAction
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


# TODO: constants file
DEFAULT_MAP = "SmallBrawlhaven"   # every match needs a locked map to start
DEFAULT_TURBO_FPS = 300.0         # render-frame rate used when realtime=False


class Match:
    """
    Gym style match over a live game instance.
    """

    def __init__(self,
                 obs_builder: Optional[ObsBuilder] = None,
                 reward_function: Optional[RewardFunction] = None,
                 terminal_conditions: Optional[Sequence[TerminalCondition]] = None,
                 action_parser: Optional[ActionParser] = None,
                 state_setter: Optional[StateSetter] = None,
                 tick_skip: int = 8,
                 realtime: bool = False,
                 render_fps: Optional[float] = None,
                 fps: float = 60.0,
                 n_players: int = 2,
                 legends: Optional[Sequence[Any]] = None,
                 map_name: Optional[str] = None,
                 auto_minimize: bool = False,
                 auto_mute: bool = False,
                 host: str = "127.0.0.1",
                 port: int = 8790):
        if brawlgym_core is None:
            raise ImportError(
                "brawlgym requires the brawlgym_core engine module; install it and ensure it is importable") from _core_import_error
        self.obs_builder = obs_builder or DefaultObs()
        self.reward_function = reward_function or CombinedReward(
            [DamageDealtReward(), KOReward(ko_reward=200.0, death_penalty=200.0)])
        self.terminal_conditions: List[TerminalCondition] = list(
            terminal_conditions if terminal_conditions is not None
            else [TeamWipeCondition(), TimeoutCondition(1200)])
        self.action_parser = action_parser or DefaultAction()
        self.state_setter = state_setter or DefaultStateSetter()
        self.tick_skip = int(tick_skip)
        self.realtime = bool(realtime)
        self.render_fps = render_fps
        self.fps = float(fps)   # native sim rate for wall-clock pacing
        self.n_players = int(n_players)
        # per-slot legends (HeroIDs or names)
        # team 1: 0,2,4,6
        # team 2: 1,3,5,7
        # None = the engine's default roster.
        self.legends: Optional[List[int]] = self._resolve_legends(legends) if legends else None
        # A match cannot start without a locked map
        # map_name=None uses small brawlhaven
        self.map_name = map_name or DEFAULT_MAP
        self.auto_minimize = bool(auto_minimize)
        self.auto_mute = bool(auto_mute)
        self.map_info = brawlgym_core.get_map_geometry(self.map_name)
        for comp in (self.obs_builder, self.state_setter):
            if hasattr(comp, "set_map_info"):
                comp.set_map_info(self.map_info)
        # NOTE: the engine's internal `framems` stays at 25ms regardless of fps - it is the
        # forced-step owed-time, chosen so exactly ONE 60fps frame runs per step (floor math
        # needs it in [16.7, 33.3)); it does not affect game speed.

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
        if self.realtime:
            self._bridge.configure(1, 25.0)     # 1x speed, rendered (native 60fps free-run)
        else:
            self._bridge.configure(max(16, self.tick_skip * 2), 25.0)
        target = self.render_fps
        if target is None and not self.realtime:
            target = DEFAULT_TURBO_FPS
        if target:
            self._bridge.set_render_fps(float(target))
            print("[brawlgym] render fps -> %g" % target, flush=True)
        self._bridge.set_sitout(True)           # deaths sit out until reset()
        self._state = st
        print("[brawlgym] match up: %d fighters" % len(st.players), flush=True)
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
        self.obs_builder.reset(st)
        self.reward_function.reset(st)
        for tc in self.terminal_conditions:
            tc.reset(st)
        # noop previous action
        zero_act = [0.0] * self.action_parser.get_action_space_size()
        return [self.obs_builder.build_obs(p, st, zero_act) for p in st.players]

    def step(self, actions: Sequence[Any]):
        """
        Advance tick_skip frames with the given per-agent actions.

        Returns (observations, rewards, terminated, game_state).
        """
        masks = self.action_parser.parse_actions(actions, self._state)
        st = GameState(self._bridge.step(masks, self.tick_skip))
        self._state = st
        self._prev_actions = actions
        obs = [self.obs_builder.build_obs(p, st, a) for p, a in zip(st.players, actions)]
        rewards = [self.reward_function.get_reward(p, st, a)
                   for p, a in zip(st.players, actions)]
        terminated = any(tc.is_terminal(st) for tc in self.terminal_conditions)
        return obs, rewards, terminated, st
