"""
Typed game state.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .. import common_values
from .player_data import PlayerData


class ItemData:
    """
    A weapon/gadget item on the stage.
    """

    __slots__ = ("name", "is_crate", "is_weapon", "is_gadget", "x", "y", "vx", "vy")

    def __init__(self, it: Dict[str, Any]):
        self.name: str = str(it.get("nm", ""))  # one of common_values.ITEM_TYPES
        self.is_crate: bool = self.name == common_values.WEAPON_CRATE
        self.is_weapon: bool = self.name in common_values.WEAPONS
        self.is_gadget: bool = self.name in common_values.GADGETS
        self.x: float = float(it.get("x", 0.0))
        self.y: float = float(it.get("y", 0.0))
        self.vx: float = float(it.get("vx", 0.0))
        self.vy: float = float(it.get("vy", 0.0))


class GameState:
    """
    Full state for one frame: every fighter + every live item.
    """

    __slots__ = ("frame", "phase", "players", "items", "raw")

    def __init__(self, st: Dict[str, Any]):
        self.frame: int = int(st.get("fr", 0))
        self.phase: int = int(st.get("ph", 0))
        self.players: List[PlayerData] = [PlayerData(f) for f in st.get("fs", [])]
        self.items: List[ItemData] = [ItemData(it) for it in st.get("it", [])]
        self.raw: Dict[str, Any] = st

    def teams(self) -> Dict[int, List[PlayerData]]:
        out: Dict[int, List[PlayerData]] = {}
        for p in self.players:
            out.setdefault(p.team, []).append(p)
        return out

    def teammates_of(self, player: PlayerData) -> List[PlayerData]:
        return [p for p in self.players if p.team == player.team and p.port != player.port]

    def opponents_of(self, player: PlayerData) -> List[PlayerData]:
        return [p for p in self.players if p.team != player.team]
