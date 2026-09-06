__version__ = '0.1.0a1'

release_notes = {
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
