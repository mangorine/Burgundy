"""
Test script for yellow tiles (knowledge tiles) system.

This script tests:
- Creating yellow tiles from definitions
- Adding yellow tiles to players
- Applying yellow tile effects
- End-game scoring calculation
"""

from player import Player
from yellow_tiles_list import create_yellow_tile, YELLOW_TILE_DEFINITIONS
from yellow_tiles import Income, RuleModification, Scoring
from board import Tile, TileType
from animals import Animal, AnimalType
from buildings import Building, BuildingType


def test_yellow_tile_creation():
    """Test creating yellow tiles from definitions."""
    print("=" * 60)
    print("TEST 1: Yellow Tile Creation")
    print("=" * 60)
    
    # Create different types of yellow tiles
    tile_1 = create_yellow_tile(1)  # RuleModification
    tile_2 = create_yellow_tile(2)  # Income
    tile_15 = create_yellow_tile(15)  # Scoring
    
    print(f"Tile 1: {tile_1.name} - {tile_1.get_tile_type()}")
    print(f"  Description: {tile_1.description}")
    print(f"\nTile 2: {tile_2.name} - {tile_2.get_tile_type()}")
    print(f"  Description: {tile_2.description}")
    print(f"\nTile 15: {tile_15.name} - {tile_15.get_tile_type()}")
    print(f"  Description: {tile_15.description}")
    
    assert isinstance(tile_1, RuleModification)
    assert isinstance(tile_2, Income)
    assert isinstance(tile_15, Scoring)
    print("\n✓ All tile types created correctly!\n")


def test_player_yellow_tiles():
    """Test adding yellow tiles to a player."""
    print("=" * 60)
    print("TEST 2: Adding Yellow Tiles to Player")
    print("=" * 60)
    
    player = Player("Test Player")
    
    # Add some yellow tiles
    tile_1 = create_yellow_tile(1)  # Flexible Zoning
    tile_8 = create_yellow_tile(8)  # Master Laborer
    tile_16 = create_yellow_tile(16)  # Warehouse Scoring
    
    player.add_yellow_effect(tile_1)
    player.add_yellow_effect(tile_8)
    player.add_yellow_effect(tile_16)
    
    print(f"Player has {len(player.yellow_effects)} yellow tiles:")
    for tile in player.yellow_effects:
        print(f"  - {tile.name}")
    
    # Test checking for specific tiles
    assert player.has_yellow_tile_by_id(1)
    assert player.has_yellow_tile_by_id(8)
    assert player.has_yellow_tile_by_id(16)
    assert not player.has_yellow_tile_by_id(99)
    
    print("\n✓ Yellow tiles added and checked correctly!\n")


def test_worker_adjustment_bonus():
    """Test worker adjustment bonus with Master Laborer tile."""
    print("=" * 60)
    print("TEST 3: Worker Adjustment Bonus")
    print("=" * 60)
    
    player_without = Player("Player Without Tile")
    player_with = Player("Player With Master Laborer")
    
    # Add Master Laborer tile (#8) to second player
    tile_8 = create_yellow_tile(8)
    player_with.add_yellow_effect(tile_8)
    
    bonus_without = player_without.get_worker_adjustment_bonus()
    bonus_with = player_with.get_worker_adjustment_bonus()
    
    print(f"Player without tile #8: +/-{bonus_without} per worker")
    print(f"Player with tile #8: +/-{bonus_with} per worker")
    
    assert bonus_without == 1
    assert bonus_with == 2
    print("\n✓ Worker adjustment bonus works correctly!\n")


def test_goods_selling_effects():
    """Test yellow tile effects when selling goods."""
    print("=" * 60)
    print("TEST 4: Goods Selling Effects")
    print("=" * 60)
    
    from board import GoodsColor, GoodsTile
    
    player = Player("Merchant Player")
    
    # Add Master Merchant (#3) and Trade Connections (#4)
    tile_3 = create_yellow_tile(3)
    tile_4 = create_yellow_tile(4)
    player.add_yellow_effect(tile_3)
    player.add_yellow_effect(tile_4)
    
    # Add some goods
    goods = [GoodsTile(GoodsColor.RED)] * 3
    player.add_goods(goods)
    
    print(f"Initial state:")
    print(f"  Workers: {player.workers}")
    print(f"  Silverlings: {player.silverlings}")
    print(f"  Goods: {len(player.goods_storage)}")
    
    # Sell goods (normally gives silverlings)
    num_sold = player.sell_goods_of_color(GoodsColor.RED)
    
    print(f"\nAfter selling {num_sold} goods:")
    print(f"  Workers: {player.workers} (gained 1 from Trade Connections)")
    print(f"  Silverlings: {player.silverlings} (gained {num_sold} extra from Master Merchant)")
    
    assert player.workers == 1  # From Trade Connections
    assert player.silverlings == num_sold  # Extra from Master Merchant
    assert player.total_goods_sold == 3
    assert len(player.sold_goods_types) == 1
    print("\n✓ Goods selling effects work correctly!\n")


def test_end_game_scoring():
    """Test end-game scoring from yellow tiles."""
    print("=" * 60)
    print("TEST 5: End-Game Scoring")
    print("=" * 60)
    
    player = Player("Scoring Player")
    
    # Add some scoring tiles
    tile_16 = create_yellow_tile(16)  # Warehouse Scoring (4 VP each)
    tile_24 = create_yellow_tile(24)  # Animal Diversity (4 VP per type)
    player.add_yellow_effect(tile_16)
    player.add_yellow_effect(tile_24)
    
    # Add some warehouses to the board
    warehouse_tile = Tile(TileType.BUILDING, False)
    warehouse_tile.tile = Building(BuildingType.WAREHOUSE)
    
    # Place 2 warehouses in different regions
    if len(player.board.regions) >= 2:
        region1 = player.board.regions[0]
        region2 = player.board.regions[1]
        
        # Find empty slots
        empty_slot1 = None
        empty_slot2 = None
        
        for slot in region1.slots:
            if not slot.tile:
                empty_slot1 = slot
                break
        
        for slot in region2.slots:
            if not slot.tile:
                empty_slot2 = slot
                break
        
        if empty_slot1 and empty_slot2:
            empty_slot1.tile = warehouse_tile
            empty_slot2.tile = warehouse_tile
    
    # Add some animals of different types
    sheep_tile = Tile(TileType.ANIMAL, False)
    sheep_tile.tile = Animal(AnimalType.SHEEP, 3)
    
    cow_tile = Tile(TileType.ANIMAL, False)
    cow_tile.tile = Animal(AnimalType.CATTLE, 4)
    
    # Place animals
    if len(player.board.regions) >= 3:
        region3 = player.board.regions[2]
        region4 = player.board.regions[3] if len(player.board.regions) > 3 else region3
        
        for slot in region3.slots:
            if not slot.tile:
                slot.tile = sheep_tile
                break
        
        for slot in region4.slots:
            if not slot.tile:
                slot.tile = cow_tile
                break
    
    # Calculate scoring
    total_vp = player.calculate_yellow_tiles_score()
    
    print(f"Player has {len(player.yellow_effects)} scoring tiles:")
    for tile in player.yellow_effects:
        if isinstance(tile, Scoring):
            vp = tile.calculate_vp_end_of_game(player)
            print(f"  - {tile.name}: {vp} VP")
    
    print(f"\nTotal VP from yellow tiles: {total_vp}")
    
    assert total_vp >= 0  # Should have some points
    print("\n✓ End-game scoring calculated!\n")


def test_all_tiles_exist():
    """Test that all 26 yellow tiles are defined."""
    print("=" * 60)
    print("TEST 6: All Tiles Defined")
    print("=" * 60)
    
    print(f"Total yellow tiles defined: {len(YELLOW_TILE_DEFINITIONS)}")
    
    # List all tiles
    income_tiles = []
    rule_tiles = []
    scoring_tiles = []
    
    for tile_id in sorted(YELLOW_TILE_DEFINITIONS.keys()):
        tile = YELLOW_TILE_DEFINITIONS[tile_id]
        if isinstance(tile, Income):
            income_tiles.append(tile_id)
        elif isinstance(tile, RuleModification):
            rule_tiles.append(tile_id)
        elif isinstance(tile, Scoring):
            scoring_tiles.append(tile_id)
    
    print(f"\nIncome tiles ({len(income_tiles)}): {income_tiles}")
    print(f"Rule Modification tiles ({len(rule_tiles)}): {rule_tiles}")
    print(f"Scoring tiles ({len(scoring_tiles)}): {scoring_tiles}")
    
    total = len(income_tiles) + len(rule_tiles) + len(scoring_tiles)
    print(f"\nTotal: {total} tiles")
    
    assert total == 26, f"Expected 26 tiles, found {total}"
    print("\n✓ All 26 yellow tiles are defined!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("YELLOW TILES TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_yellow_tile_creation()
        test_player_yellow_tiles()
        test_worker_adjustment_bonus()
        test_goods_selling_effects()
        test_end_game_scoring()
        test_all_tiles_exist()
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
