"""
Game constants shared across the package.
"""

# the game's native sim rate; game_speed is a multiple of this
NATIVE_FPS = 60.0

# every match needs a locked map to start
DEFAULT_MAP = "SmallBrawlhaven"

# render-frame rates: steps run between frames, so a low rate leaves the most room for them
UNCAPPED_RENDER_FPS = 30.0

# engine input bits, one per button
UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8
JUMP, HEAVY, LIGHT, DODGE, THROW = 16, 64, 128, 256, 512
BUTTON_BITS = (UP, DOWN, LEFT, RIGHT, JUMP, LIGHT, HEAVY, DODGE, THROW)
NUM_BUTTONS = len(BUTTON_BITS)

# team ids as reported by the engine
TEAM_1 = 1
TEAM_2 = 2

# fighters
MAX_JUMPS = 3          # ground jump + air jumps before a fighter is out of recovery options
NO_ITEM = -1           # PlayerData.held_item when nothing is held

# observation scales
POS_STD = 2000.0       # px; roughly the width of a stage
VEL_STD = 50.0         # px per frame; a full-speed jump is ~55
DAMAGE_STD = 300.0     # damage points; fighters die well before this

# SmallBrawlhaven reference values, the fallback when no map geometry is available
GROUND_Y = 1849.0
STAGE_X_MIN, STAGE_X_MAX = 600.0, 2150.0
