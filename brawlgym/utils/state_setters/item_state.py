"""
State setters: choose where every fighter starts each episode.
"""
from __future__ import annotations

import random
from typing import List, Optional, Sequence

from ..common_values import GADGETS
from ..legends import legend_weapons
from .state_setter import ItemSpawn, Position, StateSetter


class ArmedStateSetter(StateSetter):
    # TODO: maybe just merge this into the state setter interface, since it is a common enough use case to want to arm the fighters with something
    """
    Wraps another state setter and arms the fighters, either with named items or at random.

    A legend can only use its own two weapons, so a random draw picks between those two and a
    gadget: by default 45% each weapon and 10% a gadget.
    """

    def __init__(self, setter: StateSetter,
                 held: Optional[Sequence[Optional[str]]] = None,
                 items: Optional[Sequence[ItemSpawn]] = None,
                 arm_chance: float = 0.0,
                 weapon_weights: Sequence[float] = (45.0, 45.0),
                 gadget_weight: float = 10.0,
                 gadgets: Sequence[str] = GADGETS,
                 rng: Optional[random.Random] = None):
        self.setter = setter
        self.held = list(held) if held is not None else []
        self.items = list(items) if items is not None else []
        self.arm_chance = float(arm_chance)
        self.weapon_weights = tuple(weapon_weights)
        self.gadget_weight = float(gadget_weight)
        self.gadgets = tuple(gadgets)
        self.clear_items = True
        self.rng = rng or random.Random()

    def set_map_info(self, map_info) -> None:
        super().set_map_info(map_info)
        self.setter.set_map_info(map_info)

    def build_positions(self, n_players: int) -> List[Position]:
        return self.setter.build_positions(n_players)

    def build_items(self, n_players: int) -> List[ItemSpawn]:
        return list(self.items)

    def build_held(self, n_players: int, heroes: Sequence[int]) -> List[Optional[str]]:
        out: List[Optional[str]] = []
        for i in range(n_players):
            named = self.held[i] if i < len(self.held) else None
            if named:
                out.append(named)
            elif self.rng.random() < self.arm_chance:
                out.append(self._draw(heroes[i] if i < len(heroes) else -1))
            else:
                out.append(None)
        return out

    def _draw(self, hero_id: int) -> Optional[str]:
        """
        One of the legend's two weapons, or a gadget, by weight.
        """
        choices: List[str] = []
        weights: List[float] = []
        for weapon, weight in zip(legend_weapons(hero_id), self.weapon_weights):
            choices.append(weapon)
            weights.append(float(weight))
        if self.gadgets and self.gadget_weight > 0:
            choices.append(self.rng.choice(list(self.gadgets)))
            weights.append(self.gadget_weight)
        if not choices or sum(weights) <= 0:
            return None
        return self.rng.choices(choices, weights=weights, k=1)[0]
