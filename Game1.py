from board import Board, Tile, TileType
from player import Player
from random import randint


class Game:
    def __init__(self, player_names, seed=None):
        self.board = Board(seed=seed)
        self.players = [Player(name=n, layout_id=1) for n in player_names]

        # Tour / manche
        self.current_player_index = 0
        self.round = 1
        self.turn_in_round = 1
        self.white_die = None

        # État du tour
        self.turn_started = False

    # =========================
    # PROPERTIES
    # =========================
    @property
    def current_player(self):
        return self.players[self.current_player_index]

    # =========================
    # ROUND / TURN
    # =========================
    def start_new_round(self):
        """Début de manche : lancer le dé blanc (1 fois pour tous)."""
        self.white_die = randint(1, 6)
        self.turn_in_round = 1
        self.current_player_index = 0
        self.turn_started = False
        return self.white_die

    def start_turn(self):
        """Démarre le tour du joueur courant (lance ses 2 dés)."""
        p = self.current_player
        p.dice = [randint(1, 6), randint(1, 6)]
        p.used_dice = []
        self.turn_started = True
        return {
            "dice": p.dice,
            "white_die": self.white_die,
        }

    def start_turn_if_needed(self):
        if not self.turn_started:
            self.start_turn()

    def end_turn(self):
        """Passe au joueur suivant, et gère les fins de manche."""
        self.turn_started = False

        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        if self.current_player_index == 0:
            self.turn_in_round += 1
            if self.turn_in_round > len(self.players):
                self.round += 1
                self.start_new_round()

    # =========================
    # DICE MANAGEMENT
    # =========================
    def can_use_die(self, die_value: int) -> bool:
        p = self.current_player
        return die_value in p.dice and die_value not in p.used_dice

    def use_die(self, die_value: int):
        if not self.can_use_die(die_value):
            raise ValueError(
                f"Dé {die_value} indisponible "
                f"(dés={self.current_player.dice}, utilisés={self.current_player.used_dice})"
            )
        self.current_player.used_dice.append(die_value)

    def is_turn_finished(self) -> bool:
        return len(self.current_player.used_dice) >= 2

    # =========================
    # ACTIONS (liées aux dés)
    # =========================
    def action_take_tile_from_depot(self, depot_id: int, die_value: int):
        self.start_turn_if_needed()

        if not (1 <= depot_id <= 6):
            raise ValueError("Depot invalide")

        if die_value != depot_id:
            raise ValueError("Le dé doit correspondre au numéro du dépôt")

        if not self.can_use_die(die_value):
            raise ValueError("Dé non disponible")

        p = self.current_player

        if not p.can_store_hex_tile():
            raise ValueError("Stockage plein")

        tile = self.board.take_hex_from_depot(depot_id)
        p.add_hex_to_storage(tile)
        self.use_die(die_value)
        return tile

    def action_buy_black_tile(self, die_value: int):
        self.start_turn_if_needed()

        if not self.can_use_die(die_value):
            raise ValueError("Dé non disponible")

        p = self.current_player
        p.spend_silverlings(2)

        tile = self.board.take_hex_from_black_depot()

        if not p.can_store_hex_tile():
            raise ValueError("Stockage plein")

        p.add_hex_to_storage(tile)
        self.use_die(die_value)
        return tile

    def action_place_tile_from_storage(self, storage_index, coord, die_value):
        self.start_turn_if_needed()

        if not self.can_use_die(die_value):
            raise ValueError("Dé non disponible")

        p = self.current_player
        tile = p.remove_hex_from_storage(storage_index)

        result = p.board.place_tile(
            tile,
            coord,
            current_round=self.round,
            player=p,
        )

        self.use_die(die_value)
        return result

    @property
    def actions_remaining(self) -> int:
        """
        Nombre d’actions restantes = 2 dés - dés déjà utilisés
        """
        if not self.turn_started:
            return 0
        return max(0, 2 - len(self.current_player.used_dice))

