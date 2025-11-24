from abc import ABC, abstractmethod
import player

class YellowTiles(ABC):
    # of the 26 tiles, there are THREE categories
    @abstractmethod
    def __init__(self, tile_id: str, black_tile: bool, name: str, description: str,owner: player):
        self.tile_id = tile_id
        self.black_tile = False
        self.name = name
        self.description = description
        self.owner = None
    
    def on_board(self, player_id):
        self.owner = player_id
    #peut-être rajouter des méthodes mais plus tard


class Income(YellowTiles):
    # A METTRE EN ABSTRACT METHOD AUSSI?????
    # ex: when you get to gain workers or silver coins
    def __init__(self, tile_id: str, black_tile: bool, name: str, description: str,owner: player):
        super().__init__(tile_id,black_tile, name, description)

    def on_end_of_phase(self):
        ...

    def on_action(self, action_type):
        ...


class RuleModification(YellowTiles):
    # ex: add two of the same building in the same group
    def __init__(self, tile_id: str, black_tile: bool, name: str, description: str,owner: player, modification_effect: function):
        super().__init__(tile_id, name, description)
        self.modification_effect = modification_effect
        """"Maybe smt to change here, where to put this method???"""


    def apply_effect(self, action_type, data):
        # This method would be called by the game engine when a relevant action occurs
        return self.modification_effect(action_type, data)


class Scoring(YellowTiles): 
    # ex: count the numbers of buildings in the domain at the end of the game
    def __init__(self, tile_id: str, black_tile: bool, name: str, description: str, owner: player, scoring_condition):
        # à voir quel est le type de scoring condition
        super().__init__(tile_id, name, description)
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