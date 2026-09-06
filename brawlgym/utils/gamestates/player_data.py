"""
Typed game state objects.
"""
from __future__ import annotations

from typing import Any, Dict, List

class PlayerData:
    """
    One fighter's state for a single frame.
    """

    __slots__ = ("port", "team", "player_id", "x", "y", "vx", "vy", "on_ground",
                 "facing_left", "damage", "dead", "state", "dodge_cooldown",
                 "dodge_timer", "jumps_used", "held", "raw")

    def __init__(self, f: Dict[str, Any]):
        self.port: int = int(f.get("port", 0))            # 1-based port number
        self.team: int = int(f.get("team", 0))
        self.player_id: int = int(f.get("id", 0))
        self.x: float = float(f.get("x", 0.0))
        self.y: float = float(f.get("y", 0.0))
        self.vx: float = float(f.get("vx", 0.0))
        self.vy: float = float(f.get("vy", 0.0))
        self.on_ground: bool = int(f.get("air", 1)) == 0
        self.facing_left: bool = int(f.get("face", 0)) == 1
        self.damage: float = float(f.get("dmg", 0.0))
        self.dead: bool = int(f.get("dead", 0)) == 1      # KO'd this episode, now sitting out
        self.state: int = int(f.get("st", 0))             # action-state id
        self.dodge_cooldown: float = float(f.get("dcd", 0.0))
        self.dodge_timer: float = float(f.get("ddg", 0.0))
        self.jumps_used: float = float(f.get("tjmp", 0.0))
        self.held: bool = int(f.get("held", 0)) == 1      # in hitstun
        self.raw: Dict[str, Any] = f                      # full raw dict
