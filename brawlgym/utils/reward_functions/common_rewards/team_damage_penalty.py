from typing import Dict, Optional

from ...gamestates import GameState, PlayerData
from ..reward_function import RewardFunction


class TeamDamagePenalty(RewardFunction):
    """
    -1 per point of damage the agent dealt to its own team this step.

    The game's dealt/taken totals ignore friendly fire, so a teammate whose damage rose more than
    their taken total did was hit by their own team. That damage is charged to the teammates who
    were attacking at the time, split evenly.
    """

    def __init__(self):
        self._damage: Dict[int, float] = {}
        self._taken: Dict[int, float] = {}
        self._attacking: Dict[int, bool] = {}
        self._cache_state: Optional[GameState] = None
        self._cache: Dict[int, float] = {}

    def reset(self, initial_state: GameState) -> None:
        self._damage = {p.port: p.damage for p in initial_state.players}
        self._taken = {p.port: p.damage_taken for p in initial_state.players}
        self._attacking = {p.port: p.attacking for p in initial_state.players}
        self._cache_state = None

    def _compute(self, state: GameState) -> Dict[int, float]:
        out: Dict[int, float] = {p.port: 0.0 for p in state.players}
        for team, members in state.teams().items():
            for victim in members:
                d_damage = victim.damage - self._damage.get(victim.port, victim.damage)
                d_taken = victim.damage_taken - self._taken.get(victim.port, victim.damage_taken)
                friendly = max(0.0, d_damage - max(0.0, d_taken))
                if friendly <= 0.0:
                    continue
                others = [p for p in members if p.port != victim.port]
                attackers = [p for p in others if p.attacking or self._attacking.get(p.port, False)] or others
                for p in attackers:
                    out[p.port] += friendly / len(attackers)
        self._damage = {p.port: p.damage for p in state.players}
        self._taken = {p.port: p.damage_taken for p in state.players}
        self._attacking = {p.port: p.attacking for p in state.players}
        return out

    def get_reward(self, player: PlayerData, state: GameState, previous_action) -> float:
        if state is not self._cache_state:
            self._cache = self._compute(state)
            self._cache_state = state
        return -self._cache.get(player.port, 0.0)
