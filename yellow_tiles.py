from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from player import Player


@dataclass(frozen=True)
class YellowTile(ABC):
    """
    Base class for all yellow (knowledge) tiles in Castles of Burgundy.
    
    There are three categories:
    - Income: Provide resources at specific game moments
    - RuleModification: Change game rules or enhance actions
    - Scoring: Provide victory points at end of game
    
    Note: frozen=True makes these tiles immutable and hashable (usable in sets).
    """
    tile_id: int
    name: str
    description: str
    black_tile: bool = False
    
    @abstractmethod
    def get_tile_type(self) -> str:
        """Returns the type of yellow tile."""
        pass


@dataclass(frozen=True)
class Income(YellowTile):
    """
    Income tiles provide resources (workers, silverlings) at specific moments.
    
    Examples:
    - Gain 1 worker for each mine at end of phase
    - Gain 1 silverling when taking workers action
    """
    
    def get_tile_type(self) -> str:
        return "Income"
    
    def apply_end_of_phase_income(self, player: "Player") -> None:
        """
        Apply income at the end of each phase.
        Specific logic implemented by tile definitions.
        """
        pass
    
    def apply_action_income(self, player: "Player", action_type: str) -> None:
        """
        Apply income when a specific action occurs.
        Specific logic implemented by tile definitions.
        """
        pass


@dataclass(frozen=True)
class RuleModification(YellowTile):
    """
    Rule modification tiles change game mechanics or enhance player actions.
    
    Examples:
    - Place multiple buildings of same type in one city
    - Adjust die by +/-2 per worker instead of +/-1
    - Access black depot
    """
    
    def get_tile_type(self) -> str:
        return "RuleModification"
    
    def modifies_rule(self, rule_name: str) -> bool:
        """
        Check if this tile modifies a specific game rule.
        Used by game engine to check active modifications.
        """
        # Tile-specific implementations will check their tile_id
        return False


@dataclass(frozen=True)
class Scoring(YellowTile):
    """
    Scoring tiles provide victory points at the end of the game.
    
    Examples:
    - 4 VP for each Warehouse building
    - 3 VP for each different goods type sold
    - 4 VP for each different animal type
    
    Note: scoring_function must be a hashable callable (not a lambda with mutable captures).
    """
    scoring_function: Optional[Callable[["Player"], int]] = None
    
    def get_tile_type(self) -> str:
        return "Scoring"
    
    def calculate_vp_end_of_game(self, player: "Player") -> int:
        """
        Calculate victory points this tile provides at game end.
        """
        if self.scoring_function:
            return self.scoring_function(player)
        return 0


def calculate_total_yellow_tiles_vp(player: "Player") -> int:
    """
    Calculate total victory points from all scoring yellow tiles.
    Call this at the end of the game.
    """
    total_vp = 0
    for tile in player.yellow_effects:
        if isinstance(tile, Scoring):
            total_vp += tile.calculate_vp_end_of_game(player)
    return total_vp 