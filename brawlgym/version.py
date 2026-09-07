__version__ = '0.1.1'

release_notes = {
    '0.1.1': """
    - Match takes a single game_speed (1 = real time, 2 = double, 0 = uncapped) in place of
      realtime, render_fps and fps. Uncapped stepping is several times faster.
    - New DefaultObs: positions relative to the fighter and to the map's blast bounds, 16 hard
      and 16 soft stage rays, ground probes for edge distance, previous action as the buttons
      pressed.
    - utils.common_values and utils.math collect the constants and 2D helpers.
    - PlayerData.dodge_cooldown and dodging are booleans; held is now held_item and has_weapon.
    - Launch-time minimize/mute waits for every instance window instead of giving up early.
    """,
    '0.1.0': """
    - First usable release: the engine bridge ships inside the package, brawlgym.inject() patches
      the game, and LookupAction is available for discrete policies.
    """,
    '0.1.0a1': """
    - Initial alpha release. The public API surface only: Match/make(), obs builders, reward
      functions, terminal conditions, action parsers, state setters, and the game launcher.
    - NOT yet usable for training. The engine bridge (brawlgym_core) is not published, so
      Match.connect() and friends will raise.
    """,
}


def get_current_release_notes():
    if __version__ in release_notes:
        return release_notes[__version__]
    return ''


def print_current_release_notes():
    print(f"Version {__version__}")
    print(get_current_release_notes())
    print("")
