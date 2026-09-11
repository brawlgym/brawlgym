"""
Typed game state objects.
"""
from __future__ import annotations

from typing import Any, Dict

from .. import common_values
from ..legends import hero_id_for, legend_name, legend_weapons


class PlayerData:
    """
    One fighter's state for a single frame.
    """

    __slots__ = ("port", "team", "player_id", "x", "y", "vx", "vy", "on_ground",
                 "facing_left", "damage", "dead", "state", "dodge_cooldown",
                 "dodging", "jumps_used", "wall_side", "held_item", "has_weapon", "attacking", "stunned",
                 "hits_taken", "damage_dealt", "damage_taken", "hero_name", "hero_id", "raw")

    def __init__(self, f: Dict[str, Any]):
        self.port: int = int(f.get("port", 0))                              # 1-based port number
        self.team: int = int(f.get("team", 0))
        self.player_id: int = int(f.get("id", 0))
        self.x: float = float(f.get("x", 0.0))
        self.y: float = float(f.get("y", 0.0))
        self.vx: float = float(f.get("vx", 0.0))
        self.vy: float = float(f.get("vy", 0.0))
        self.on_ground: bool = int(f.get("air", 1)) == 0
        self.facing_left: bool = int(f.get("face", 0)) == 1
        self.damage: float = float(f.get("dmg", 0.0))
        self.dead: bool = int(f.get("dead", 0)) == 1                        # KO'd this episode, now sitting out
        self.state: int = int(f.get("st", 0))                               # action-state id
        self.dodge_cooldown: bool = int(f.get("dcd", 0)) == 1               # dodge is on cooldown
        self.dodging: bool = int(f.get("ddg", 0)) == 1                      # committed in a dodge
        self.jumps_used: int = int(f.get("tjmp", 0))                        # air jumps/recoveries since last grounded
        self.wall_side: int = int(f.get("wall", 0))                         # 0 none, 1 wall on the right, 2 on the left
        self.held_item: str = str(f.get("hnm", common_values.NO_ITEM))      # weapon/gadget name, NO_ITEM if empty-handed
        self.has_weapon: bool = self.held_item in common_values.WEAPONS
        self.attacking: bool = int(f.get("atk", 0)) == 1                    # inside an attack animation
        self.stunned: bool = int(f.get("stn", 0)) == 1                      # in hitstun, inputs are ignored
        self.hits_taken: int = int(f.get("hit", 0))                         # hits received during the last step
        self.damage_dealt: float = float(f.get("dlt", 0.0))                 # running total for the match
        self.damage_taken: float = float(f.get("tkn", 0.0))                 # running total; unlike damage it never resets
        self.hero_name: str = str(f.get("hero", ""))                        # the game's HeroName
        self.hero_id: int = hero_id_for(self.hero_name)                     # which legend this is
        self.raw: Dict[str, Any] = f                                        # full raw dict

    @property
    def on_wall(self) -> bool:
        """
        Clinging to a wall. Touching one restores stamina (aerial jumps/recoveries) the same
        way the ground does, but jumps_used does NOT reset for a wall - so this is what
        tells you the stamina came back.
        """
        return self.wall_side != 0

    @property
    def legend(self) -> str:
        """
        The legend's display name.
        """
        return legend_name(self.hero_id)

    @property
    def weapons(self) -> tuple:
        """
        The two weapons this legend can use.
        """
        return legend_weapons(self.hero_id)
