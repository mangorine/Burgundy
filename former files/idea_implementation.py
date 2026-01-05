from yellow_tiles import *
from yellow_tiles_list import *
from players import *

import random

class Game:
    def __init__(self):
        self.yellow_tile_draw_pile = []
        self.game_board_depots = {} # e.g., {1: tile, 2: tile, ...}
        self.players = [] # List of player objects

    def setup_game(self, player_names, tile_ids_in_game):
        """
        Initializes the game, creates all tiles, and shuffles them.
        """
        # 1. Create one instance of each yellow tile needed for the game
        all_tiles = [create_yellow_tile(tid) for tid in tile_ids_in_game]
        
        # 2. Shuffle them to create the draw pile
        random.shuffle(all_tiles)
        self.yellow_tile_draw_pile = all_tiles
        
        # 3. Create players
        self.players = [Player(name) for name in player_names]

        print(f"Game setup complete. {len(self.yellow_tile_draw_pile)} yellow tiles in the draw pile.")

    def restock_board(self):
        """
        Called at the start of a round to place new tiles on the board.
        """
        # Example: restock depot #5
        if self.yellow_tile_draw_pile: # Make sure the pile isn't empty
            tile_to_place = self.yellow_tile_draw_pile.pop()
            self.game_board_depots[5] = tile_to_place
            print(f"Placed '{tile_to_place.name}' in depot 5.")

# --- Player Class ---
class Player:
    def __init__(self, name):
        self.name = name
        self.yellow_tiles = [] # A list is perfect for holding a player's owned tiles

    def acquire_yellow_tile(self, tile):
        print(f"{self.name} acquired '{tile.name}'.")
        # The tile is now owned by the player and its ongoing effects are active
        self.yellow_tiles.append(tile)
        # The game engine will call the on_place method when the player places it