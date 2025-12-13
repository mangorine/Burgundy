"""
Yellow Tiles (Knowledge Tiles) Definitions for Castles of Burgundy.

This module contains all 26 yellow tile definitions with their effects.
Tiles are organized by type: Income, RuleModification, and Scoring.
"""

from yellow_tiles import Income, RuleModification, Scoring
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player


# ============================================================================
# YELLOW TILE DEFINITIONS - All 26 tiles from Castles of Burgundy
# ============================================================================

YELLOW_TILE_DEFINITIONS = {
    # ===== RULE MODIFICATION TILES =====
    1: RuleModification(
        tile_id=1,
        name="Flexible Zoning",
        description="Allows multiple buildings of the same type to be placed in a single city."
    ),
    
    3: RuleModification(
        tile_id=3,
        name="Master Merchant",
        description="Receive 2 Silverlings instead of 1 for each good sold."
    ),
    
    5: RuleModification(
        tile_id=5,
        name="Advanced Shipping",
        description="When adding a ship, take goods from two neighboring spaces instead of one."
    ),
    
    6: RuleModification(
        tile_id=6,
        name="Market Access",
        description="May buy from any of the seven depots (including the black depot)."
    ),
    
    7: RuleModification(
        tile_id=7,
        name="Animal Husbandry",
        description="Gain 1 additional victory point for each animal tile placed."
    ),
    
    8: RuleModification(
        tile_id=8,
        name="Master Laborer",
        description="Adjust a die result by +/- 2 per worker paid (instead of +/- 1)."
    ),
    
    9: RuleModification(
        tile_id=9,
        name="Free Architecture",
        description="Adjust die roll by +/- 1 when placing buildings for free (without workers)."
    ),
    
    10: RuleModification(
        tile_id=10,
        name="Free Seafaring & Husbandry",
        description="Adjust die roll by +/- 1 when placing ships or animals for free (without workers)."
    ),
    
    11: RuleModification(
        tile_id=11,
        name="Free Civic Development",
        description="Adjust die roll by +/- 1 when placing castles, mines, or knowledge tiles for free (without workers)."
    ),
    
    12: RuleModification(
        tile_id=12,
        name="Supply Chain Expertise",
        description="Adjust die roll by +/- 1 when taking new six-sided tiles from the board for free (without workers)."
    ),
    
    14: RuleModification(
        tile_id=14,
        name="Mass Recruitment",
        description="Receive 4 workers instead of 2 for the 'Take worker tiles' action."
    ),
    
    # ===== INCOME TILES =====
    2: Income(
        tile_id=2,
        name="Mine Foreman",
        description="Gain 1 worker for each of your mines at the end of each phase."
    ),
    
    4: Income(
        tile_id=4,
        name="Trade Connections",
        description="Gain 1 worker each time you sell goods."
    ),
    
    13: Income(
        tile_id=13,
        name="Recruitment Bonus",
        description="Gain 1 Silverling in addition to the workers for the 'Take worker tiles' action."
    ),
    
    # ===== SCORING TILES =====
    15: Scoring(
        tile_id=15,
        name="Goods Diversity Scoring",
        description="Gain 3 VP at the end of the game for each type of good you have sold.",
        scoring_function=lambda p: count_unique_goods_types_sold(p) * 3
    ),
    
    16: Scoring(
        tile_id=16,
        name="Warehouse Scoring",
        description="4 VP for each Warehouse.",
        scoring_function=lambda p: count_buildings_of_type(p, "warehouse") * 4
    ),
    
    17: Scoring(
        tile_id=17,
        name="Watchtower Scoring",
        description="4 VP for each Watchtower building.",
        scoring_function=lambda p: count_buildings_of_type(p, "watchtower") * 4
    ),
    
    18: Scoring(
        tile_id=18,
        name="Carpenter's Workshop Scoring",
        description="4 VP for each Carpenter's Workshop building.",
        scoring_function=lambda p: count_buildings_of_type(p, "carpenter's workshop") * 4
    ),
    
    19: Scoring(
        tile_id=19,
        name="Church Scoring",
        description="4 VP for each Church building.",
        scoring_function=lambda p: count_buildings_of_type(p, "church") * 4
    ),
    
    20: Scoring(
        tile_id=20,
        name="Market Scoring",
        description="4 VP for each Market building.",
        scoring_function=lambda p: count_buildings_of_type(p, "market") * 4
    ),
    
    21: Scoring(
        tile_id=21,
        name="Boarding House Scoring",
        description="4 VP for each Boarding House.",
        scoring_function=lambda p: count_buildings_of_type(p, "boarding house") * 4
    ),
    
    22: Scoring(
        tile_id=22,
        name="Bank Scoring",
        description="4 VP for each Bank building.",
        scoring_function=lambda p: count_buildings_of_type(p, "bank") * 4
    ),
    
    23: Scoring(
        tile_id=23,
        name="City Hall Scoring",
        description="4 VP for each City Hall building.",
        scoring_function=lambda p: count_buildings_of_type(p, "city hall") * 4
    ),
    
    24: Scoring(
        tile_id=24,
        name="Animal Diversity Scoring",
        description="Gain 4 VP at the end of the game for each different animal type on your estate.",
        scoring_function=lambda p: count_unique_animal_types(p) * 4
    ),
    
    25: Scoring(
        tile_id=25,
        name="Goods Volume Scoring",
        description="Gain 1 VP at the end of the game for each individual sold goods tile.",
        scoring_function=lambda p: count_total_goods_sold(p) * 1,
        black_tile=True
    ),
    
    26: Scoring(
        tile_id=26,
        name="Bonus Tile Scoring",
        description="Gain 2 VP at the end of the game for each bonus tile claimed.",
        scoring_function=lambda p: count_bonus_tiles(p) * 2
    )
}


# ============================================================================
# HELPER FUNCTIONS FOR SCORING TILES
# ============================================================================

def count_buildings_of_type(player: "Player", building_type: str) -> int:
    """Count how many buildings of a specific type the player has."""
    count = 0
    for region in player.board.regions:
        for slot in region.slots:
            if slot.tile and hasattr(slot.tile, 'tile'):
                building = slot.tile.tile
                if hasattr(building, 'building_type'):
                    if building.building_type.value == building_type:
                        count += 1
    return count


def count_unique_animal_types(player: "Player") -> int:
    """Count how many different animal types the player has."""
    animal_types = set()
    for region in player.board.regions:
        for slot in region.slots:
            if slot.tile and hasattr(slot.tile, 'tile'):
                animal = slot.tile.tile
                if hasattr(animal, 'animal_type'):
                    animal_types.add(animal.animal_type)
    return len(animal_types)


def count_unique_goods_types_sold(player: "Player") -> int:
    """Count how many different types of goods the player has sold."""
    # This requires tracking sold goods - implement based on your game logic
    # For now, return 0 as placeholder
    if hasattr(player, 'sold_goods_types'):
        return len(player.sold_goods_types)
    return 0


def count_total_goods_sold(player: "Player") -> int:
    """Count total number of goods tiles sold."""
    if hasattr(player, 'total_goods_sold'):
        return player.total_goods_sold
    return 0


def count_bonus_tiles(player: "Player") -> int:
    """Count how many bonus tiles the player has claimed."""
    if hasattr(player, 'bonus_tiles'):
        return len(player.bonus_tiles)
    return 0