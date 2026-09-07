"""
brawlgym - a reinforcement-learning environment for Brawlhalla.

Match drives a live game instance in deterministic lockstep, and you plug
in your own ObsBuilder / RewardFunction / TerminalCondition / ActionParser / StateSetter.

    import brawlgym

    env = brawlgym.make()
    env.connect()                # game running, match started
    obs = env.reset()
    while True:
        obs, rewards, done, state = env.step(actions)
        if done:
            obs = env.reset()

Package layout:
    brawlgym.envs                       Match
    brawlgym.utils.gamestates           GameState, PlayerData, ItemData
    brawlgym.utils.obs_builders         ObsBuilder, DefaultObs
    brawlgym.utils.reward_functions     RewardFunction, common rewards
    brawlgym.utils.terminal_conditions  TerminalCondition, TeamWipe/Timeout
    brawlgym.utils.action_parsers       ActionParser, DefaultAction, LookupAction
    brawlgym.utils.state_setters        StateSetter, Default/Random
    brawlgym.utils.common_values        game constants and observation scales
    brawlgym.utils.math                 2D helpers (raycast)
"""
from .envs import Match
from .utils.action_parsers import ActionParser, DefaultAction, LookupAction
from .utils.gamestates import GameState, ItemData, PlayerData
from .utils.obs_builders import DefaultObs, ObsBuilder
from .utils.reward_functions import CombinedReward, ConstantReward, DamageDealtReward, DamageTakenPenalty, KOReward, RewardFunction
from .utils.state_setters import DefaultStateSetter, RandomStateSetter, StateSetter
from .utils.terminal_conditions import TeamWipeCondition, TerminalCondition, TimeoutCondition
from .version import __version__


def make(**kwargs) -> Match:
    """
    Create a Match with default components (override any via kwargs).
    """
    return Match(**kwargs)


def inject(game_dir=None, refresh=False):
    """
    Patch the local Brawlhalla install with the hook built for its exact game build,
    fetching it if not already cached. Run once before launching the game for training.
    """
    from . import patcher
    return patcher.inject(game_dir=game_dir, refresh=refresh)


def set_map(name):
    """
    Lock the game to one map. Written to disk; takes effect at the next launch.
    """
    from .envs.match import brawlgym_core
    return brawlgym_core.set_map(name)


def restore_maps():
    """
    Undo set_map and put the pristine map set back.
    """
    from .envs.match import brawlgym_core
    return brawlgym_core.restore_maps()


def list_maps():
    """
    [(level_id, level_name)] - every map usable as make(map_name=...).
    """
    from .envs.match import brawlgym_core
    return brawlgym_core.list_maps()


def list_legends():
    """
    [(hero_id, hero_name, bio_name)] - every legend usable in make(legends=[...]).
    """
    from .envs.match import brawlgym_core
    return brawlgym_core.list_legends()
