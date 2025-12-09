from yellow_tiles import *
EXPANSION_TILE_DEFINITIONS = {
     1: (RuleModification, "Flexible Zoning", "Allows multiple buildings of the same type to be placed in a single city."), # type: ignore
     2: (Income, "Mine Foreman", "Gain 1 worker for each of your mines at the end of each phase."), # type: ignore
     3: (RuleModification, "Master Merchant", "Receive 2 Silverlings instead of 1 for each good sold."), # type: ignore
     4: (Income, "Trade Connections", "Gain 1 worker each time you sell goods."), # type: ignore
     5: (RuleModification, "Advanced Shipping", "When adding a ship, take goods from two neighboring spaces instead of one."), # type: ignore
     6: (RuleModification, "Market Access", "May buy from any of the seven depots (including the black depot)."), # type: ignore
     7: (RuleModification,black_tile = True, "Animal Husbandry", "Gain 1 additional victory point for each animal tile placed."),
     8: (RuleModification, "Master Laborer", "Adjust a die result by +/- 2 per worker paid (instead of +/- 1)."),
     9: (RuleModification, "Free Architecture", "Adjust die roll by +/- 1 when placing buildings for free (without workers)."),
     10: (RuleModification, "Free Seafaring & Husbandry", "Adjust die roll by +/- 1 when placing ships or animals for free (without workers)."),
     11: (RuleModification, "Free Civic Development", "Adjust die roll by +/- 1 when placing castles, mines, or knowledge tiles for free (without workers)."),
     12: (RuleModification,black_tile = True, "Supply Chain Expertise", "Adjust die roll by +/- 1 when taking new six-sided tiles from the board for free (without workers)."),
     13: (Income, "Recruitment Bonus", "Gain 1 Silverling in addition to the workers for the 'Take worker tiles' action."),
     14: (RuleModification,black_tile = True, "Mass Recruitment", "Receive 4 workers instead of 2 for the 'Take worker tiles' action."),
     15: (Scoring, "Goods Diversity Scoring", "Gain 3 VP at the end of the game for each type of good you have sold.",
         lambda p: p.sold_goods.count_unique_types() * 3),
     16: (Scoring, "Warehouse Scoring", "4 VP for each Warehouse.",
         lambda p: p.estate.count_building_type("Warehouse") * 4),
     17: (Scoring, "Watchtower Scoring", "4 VP for each Watchtower building.",
         lambda p: p.estate.count_building_type("Watchtower") * 4),
     18: (Scoring, "Carpenter's Workshop Scoring", "4 VP for each Carpenter's Workshop building.",
         lambda p: p.estate.count_carpenters_workshop() * 4),
     19: (Scoring, "Church Scoring", "4 VP for each Church building.",
         lambda p: p.estate.count_building_type("Church") * 4),
     20: (Scoring, "Market Scoring", "4 VP for each Market building.",
         lambda p: p.estate.count_building_type("Market") * 4),
     21: (Scoring, "Boarding House Scoring", "4 VP for each Boarding House.",
         lambda p: p.estate.count_building_type("Boarding House") * 4),
     22: (Scoring, "Bank Scoring", "4 VP for each Bank building.",
         lambda p: p.estate.count_building_type("Bank") * 4),
     23: (Scoring, "City Hall", "4 VP for each City Hall building.",
         lambda p: p.estate.count_building_type("City Hall") * 4),
     24: (Scoring, black_tile = True, "Animal Diversity Scoring", "Gain 4 VP at the end of the game for each different animal type on your estate.",
         lambda p: p.estate.count_unique_animal_types() * 4),
     25: (Scoring, black_tile = True, "Goods Volume Scoring", "Gain 1 VP at the end of the game for each individual sold goods tile.",
         lambda p: p.sold_goods.count_total_tiles() * 1),
     26: (Scoring, "Bonus Tile Scoring", "Gain 2 VP at the end of the game for each bonus tile claimed.",
          lambda p: p.count_bonus_tiles() * 2)
}

def create_yellow_tile(tile_id):
    """
    Factory that creates a yellow tile object using the central registry.
    """
    if tile_id not in YELLOW_TILE_DEFINITIONS:
        raise ValueError(f"No yellow tile definition found for ID: {tile_id}")

    # Unpack the data from our registry
    tile_data = YELLOW_TILE_DEFINITIONS[tile_id]
    TileClass, name, description = tile_data[0], tile_data[1], tile_data[2]
    
    # If there's extra logic (like for scoring tiles), pass it to the constructor
    if len(tile_data) > 3:
        extra_logic = tile_data[3]
        return TileClass(tile_id, name, description, extra_logic)
    else:
        return TileClass(tile_id, name, description)