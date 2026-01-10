from abc import ABC, abstractmethod

class YellowTiles(ABC):
    # of the 26 tiles, there are THREE categories
    @abstractmethod
    def __init__(self, tile_id: int, name: str, description: str, black_tile: bool = False):
        self.tile_id = tile_id
        self.black_tile = black_tile
        self.name = name
        self.description = description
    
    def on_board(self, player_id):
        self.owner = player_id
    #peut-être rajouter des méthodes mais plus tard


class Income(YellowTiles):
    # A METTRE EN ABSTRACT METHOD AUSSI?????
    # ex: when you get to gain workers or silver coins
    def __init__(self, tile_id: int, name: str, description: str, black_tile: bool = False):
        super().__init__(tile_id, name, description, black_tile)

    def on_end_of_phase(self):
        ...

    def on_action(self, action_type):
        ...


class RuleModification(YellowTiles):
    # ex: add two of the same building in the same group
    def __init__(self, tile_id: int, name: str, description: str, modification_effect: function, black_tile: bool = False):
        super().__init__(tile_id, name, description, black_tile)
        self.modification_effect = modification_effect
        """"Maybe smt to change here, where to put this method???"""


    def apply_effect(self, action_type, data):
        # This method would be called by the game engine when a relevant action occurs
        return self.modification_effect(action_type, data)


class Scoring(YellowTiles): 
    # ex: count the numbers of buildings in the domain at the end of the game
    def __init__(self, tile_id: int, name: str, description: str, scoring_condition, black_tile: bool = False):
        # à voir quel est le type de scoring condition
        super().__init__(tile_id, name, description, black_tile)
        self.scoring_condition = scoring_condition  
        # make a method to count how many of the buildings he got in his domain
        """"Maybe smt to change here, where to put this method???"""

    def calculate_vp_end_of_game(self):
        if self.owner:
            return self.scoring_condition(self.owner) 
        return 0
 
# for the class ScoringYellowTile:
total_yellow_tiles_vp = 0
for tile in player.yellow_tiles:
    if isinstance(tile,ScoringYellowTile):
        total_yellow_tiles_vp += calculate_vp_end_of_game() 