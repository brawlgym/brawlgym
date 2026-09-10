"""
Game constants shared across the package.
"""

# the game's native sim rate; game_speed is a multiple of this
NATIVE_FPS = 60.0

# every match needs a locked map to start
DEFAULT_MAP = "SmallBrawlhaven"
MAP_ENV_VAR = "BRAWLGYM_MAP"

# render-frame rates: steps run between frames, so a low rate leaves the most room for them
UNCAPPED_RENDER_FPS = 30.0

# engine input bits, one per button
UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8
JUMP, HEAVY, LIGHT, DODGE, THROW = 16, 64, 128, 256, 512
BUTTON_BITS = (UP, DOWN, LEFT, RIGHT, JUMP, LIGHT, HEAVY, DODGE, THROW)
BUTTON_NAMES = ("up", "down", "left", "right", "jump", "light", "heavy", "dodge", "throw")
NUM_BUTTONS = len(BUTTON_BITS)

# team ids as reported by the engine
TEAM_1 = 1
TEAM_2 = 2

# fighters
MAX_JUMPS = 3  # ground jump + air jumps before a fighter is out of recovery options
NO_ITEM = ""   # PlayerData.held_item when nothing is held

# TODO: I feel these are fairly self-explanatory for people who play the game, but maybe they should be in a separate file for clarity with display names
WEAPON_CRATE = "WeaponCrate"  # an unclaimed weapon spawn; becomes the picker's weapon on pickup
WEAPONS = ("Axe", "Boots", "Bow", "Cannon", "Chakram", "Fists", "Greatsword", "Hammer", "Katar", "Orb",
           "Pistol", "RocketLance", "Scythe", "Spear", "Sword")
GADGETS = ("BouncyBomb", "ProxMine", "SpikeBall", "SpawnBotFlyby", "BoomerangHoming", "StickyBomb", "BubbleBomb")
ITEM_TYPES = (WEAPON_CRATE,) + WEAPONS + GADGETS

# item spawning: https://brawlhalla.wiki.gg/wiki/Item_Spawning#When_Items_Spawn
# the game keeps at most floor(MaxItemCountMultiplier * players + MaxItemCountFixed) items on stage,
# tracked separately for weapons and gadgets. (multiplier, fixed) per Standard spawn-rate setting.
WEAPON_SPAWN_CAPS = {"low": (1.0, 0), "medium": (1.0, 1), "high": (2.0, 0)}
GADGET_SPAWN_CAPS = {"low": (0.5, 1), "medium": (1.0, 2), "high": (2.5, 0)}
DEFAULT_SPAWN_RATE = "medium"


def max_items_on_stage(n_players: int, rate: str = DEFAULT_SPAWN_RATE) -> int:
    """
    Most weapons plus gadgets that can be loose on the stage at once for this roster size.
    """
    weapons = int(WEAPON_SPAWN_CAPS[rate][0] * n_players + WEAPON_SPAWN_CAPS[rate][1])
    gadgets = int(GADGET_SPAWN_CAPS[rate][0] * n_players + GADGET_SPAWN_CAPS[rate][1])
    return weapons + gadgets

# observation scales
POS_STD = 2000.0       # px; roughly the width of a stage
VEL_STD = 50.0         # px per frame; a full-speed jump is ~55
DAMAGE_STD = 300.0     # damage points; fighters die well before this

# SmallBrawlhaven reference values, the fallback when no map geometry is available
GROUND_Y = 1849.0
STAGE_X_MIN, STAGE_X_MAX = 600.0, 2150.0
