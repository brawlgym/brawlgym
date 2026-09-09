__version__ = '0.1.2'

release_notes = {
    '0.1.2': """
    - PlayerData gains attacking, stunned, hits_taken, damage_dealt and damage_taken, read from the
      game's own fighter flags and running totals.
    - New rewards: WhiffPenalty, ComboReward, TeamDamagePenalty, VelocityReward, GroundedPenalty, one
      file each under reward_functions/common_rewards.
      DamageDealtReward and DamageTakenPenalty use the per-fighter totals, so damage is credited to
      the fighter who landed it.
    - The engine's light and heavy input bits were labelled backwards; LIGHT and HEAVY now match the game.
    - Items: GameState.items and PlayerData.held_item report the game's item names, DefaultObs
      one-hots them, Match.clear_items / spawn_item / give_item control what is on the stage and in
      the fighters' hands, and state setters can declare the same through build_items / build_held
      (see ArmedStateSetter, which can arm fighters at random by legend). give_item hands the item
      over the way the game does on a pickup, so it is instant and works in mid-air; it refuses a
      weapon the legend cannot use unless force=True.
    - PlayerData reports hero_id, legend and weapons, and DefaultObs one-hots the legend. The full
      legend table is in utils.legends (regenerate with brawlgym-core/demos/dump_legends.py).
    """,
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
