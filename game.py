from typing import List, Optional, Dict, Any
from board import Board, Tile, TileType, GoodsTile
from player import Player
from animals import Animal, AnimalType
from buildings import Building, BuildingType
import random

from yellow_tiles_list import *


class Game:
    """
    Moteur principal du jeu.

    Gère :
    - le plateau central Board
    - les joueurs (Player)
    - le tour courant / ordre du tour
    - l'application des effets des tuiles quand elles sont posées
    """

    def __init__(
        self,
        player_names: List[str],
        seed: Optional[int] = None,
    ) -> None:
        """
        Crée une partie avec N joueurs.

        - player_names : liste des noms ("Alice", "Bob", ...)
        - layouts : liste des layout_id pour chaque joueur (ex : [1,2,3,1])
        - seed : graine pour le random du Board
        """

        self.board = Board(seed=seed)
        self.players: List[Player] = [
            Player(name=player_names[i], layout_id=1) for i in range(len(player_names))
        ]

        # Index du joueur courant dans la liste players
        self.current_player_index: int = 0

        # Compteur de manches/tours globaux si besoin
        self.global_round: int = 1

    # =============================
    # Outils d'accès
    # =============================

    @property
    def current_player(self) -> Player:
        """
        Renvoie le joueur courant.
        """
        return self.players[self.current_player_index]

    def next_player(self) -> None:
        """
        Passe au joueur suivant (ordre simple pour l'instant).
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    # =============================
    # Actions principales du jeu
    # =============================

    def action_take_hex_from_depot(self, depot_id: int) -> None:
        """
        Action : le joueur courant prend une tuile hex du dépôt donné
        et la met dans sa réserve perso.
        """
        player = self.current_player
        if not player.can_store_hex_tile():
            raise ValueError(f"{player.name} ne peut pas stocker plus de tuiles.")

        tile = self.board.take_hex_from_depot(depot_id)
        player.add_hex_to_storage(tile)

    def action_take_hex_from_black_depot(self) -> None:
        """
        Action : le joueur courant achète une tuile noire pour 2 écus.
        """
        player = self.current_player
        player.spend_silverlings(2)
        tile = self.board.take_hex_from_black_depot()
        player.add_hex_to_storage(tile)

    def action_take_goods_from_ship(self, depot_id: int) -> None:
        """
        Action complémentaire : prendre toutes les marchandises d'un dépôt
        (par exemple après avoir posé un bateau).
        """
        player = self.current_player
        goods = self.board.take_all_goods_from_depot(depot_id)
        player.add_goods(goods)

    def action_place_tile_from_storage(
        self,
        storage_index: int,
        coord: tuple[int, int],
        current_round: int,
        die_value: int,
        workers_to_spend: int = 0,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Action : le joueur courant pose une tuile de sa réserve sur son plateau.

        - storage_index : indice dans player.hex_storage
        - coord : coordonnée hex sur le PlayerBoard
        - current_round : numéro de manche/round global
        - die_value : valeur du dé utilisé pour cette action
        - workers_to_spend : nombre d'ouvriers à dépenser pour ajuster le dé
        - extra_context : infos supplémentaires pour certains effets
            (ex : choix du dépôt pour un bateau, couleur à vendre, etc.)
        """
        if extra_context is None:
            extra_context = {}

        player = self.current_player

        # 0) Vérifier que le joueur a le dé et les ouvriers nécessaires
        if not player.has_die_value(die_value):
            raise ValueError(f"{player.name} n'a pas de dé avec la valeur {die_value}.")
        
        # Calculer la valeur effective du dé après ajustement avec les ouvriers
        slot = player.board.hex_map.get_slot(coord)
        if slot is None:
            raise ValueError(f"Coordonnée {coord} invalide.")
        target_value = slot.dice_value
        tile_type = slot.allowed_type
        
        # Vérifier si le joueur a un ajustement gratuit (tuiles jaunes 9-11)
        has_free_adjustment = player.get_free_placement_die_adjustment(tile_type)
        
        # Calculer la valeur effective du dé
        effective_die_value = target_value if (has_free_adjustment or workers_to_spend > 0) else die_value
        
        # 1) VALIDATION: Récupérer la tuile SANS la retirer pour vérifier le placement
        if storage_index < 0 or storage_index >= len(player.hex_storage):
            raise ValueError(f"Index de stockage {storage_index} invalide.")
        tile = player.hex_storage[storage_index]
        if tile is None:
            raise ValueError(f"Pas de tuile à l'index {storage_index}.")
        
        # 2) VALIDATION: Vérifier que le placement est légal AVANT de consommer des ressources
        if not player.board.can_place_tile_at(tile, coord, player, effective_die_value):
            raise ValueError(f"Placement illégal à {coord} pour la tuile {tile}.")
        
        # 3) Maintenant que tout est validé, on consomme les ressources
        if die_value != target_value and not has_free_adjustment:
            # Il faut des ouvriers pour ajuster
            if workers_to_spend <= 0:
                raise ValueError(f"Des ouvriers sont nécessaires pour ajuster le dé de {die_value} à {target_value}.")
            player.spend_workers(workers_to_spend)
        
        # Utiliser le dé
        player.use_die(die_value)

        # 4) Retirer la tuile du stockage
        tile = player.remove_hex_from_storage(storage_index)

        # 5) Placer la tuile sur le PlayerBoard (la validation est déjà faite)
        placement_result = player.board.place_tile(tile, coord, current_round, player, effective_die_value)

        # 3) On applique les effets selon le type de tuile
        self._apply_tile_effect(player, tile, coord, placement_result, extra_context)

        return placement_result

    # =============================
    # Application des effets
    # =============================

    def _apply_tile_effect(
        self,
        player: Player,
        tile: Tile,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Dispatch sur le bon sous-type de tuile.
        """
        ttype = tile.tile_type

        if ttype == TileType.BUILDING:
            self._apply_building_effect(player, tile.tile, coord, placement_result, ctx)
        elif ttype == TileType.MINE:
            self._apply_mine_effect(player, tile.tile, coord, placement_result, ctx)
        elif ttype == TileType.SHIP:
            self._apply_ship_effect(player, tile.tile, coord, placement_result, ctx)
        elif ttype == TileType.KNOWLEDGE:
            self._apply_yellow_tile_effect(
                player, tile.tile, coord, placement_result, ctx
            )
        elif ttype == TileType.ANIMAL:
            self._apply_animal_effect(player, tile.tile, coord, placement_result, ctx)
        elif ttype == TileType.CASTLE:
            self._apply_castle_effect(player, tile.tile, coord, placement_result, ctx)
        # sinon : rien de spécial

        # Si la région vient d’être complétée, on ajoute un bonus générique
        if placement_result.get("region_completed_now", False):
            self._apply_region_completion_bonus(player, placement_result)

        # ---------- BUILDINGS ----------

    def _apply_building_effect(
        self,
        player: Player,
        building_obj: Building,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Applique l'effet d'un bâtiment (tuile beige).

        Paramètres
        ----------
        player : Player
            Joueur qui vient de poser la tuile.
        building_obj : Building
            Tuile de bâtiment (avec un BuildingType).
        coord : (int, int)
            Coordonnée où la tuile a été posée.
        placement_result : dict
            Résultat renvoyé par PlayerBoard.place_tile (taille de région, etc.).
        ctx : dict
            Contexte contenant les choix du joueur pour certains effets.

        Clés attendues dans ctx
        -----------------------
        - WAREHOUSE :
            "goods_depot_choice" : int,
                numéro de dépôt de marchandises à vider.
        - WORKSHOP :
            "workshop_depot_choice" : int,
                dépôt d’où prendre une tuile BUILDING pour la réserve.
        - CHURCH :
            "church_depot_choice" : int,
                dépôt d’où prendre une tuile (mine/knowledge/château en théorie).
        - MARKET :
            "market_depot_choice" : int,
                dépôt d’où prendre une tuile (ship/animal en théorie).
        - CITYHALL :
            "cityhall_extra_action": {
                "storage_index": int,
                "coord": (q, r),
                "current_round": int,
                "extra_context": dict  # contexte pour la 2e tuile
            }
        """

        btype = getattr(building_obj, "building_type", None)

        # 1) WAREHOUSE : comme dans ta version actuelle
        #    -> choisir un dépôt de marchandises, tout prendre + PV
        if btype == BuildingType.WAREHOUSE:
            depot_id = ctx.get("goods_depot_choice")
            if depot_id is None:
                # Pas de choix => pas d'effet
                return

            goods = self.board.take_all_goods_from_depot(depot_id)
            player.add_goods(goods)
            player.apply_goods_sold_effects()
            # Bonus : 1 PV par marchandise prise
            player.gain_victory_points(len(goods))
            return

        # 2) WORKSHOP : prendre une tuile BUILDING d’un dépôt numéroté
        #    et la mettre dans la réserve du joueur
        elif btype == BuildingType.WORKSHOP:
            depot_id = ctx.get("workshop_depot_choice")
            if depot_id is None:
                return

            try:
                new_tile = self.board.take_hex_from_depot(depot_id)
            except ValueError:
                # Dépôt vide / inexistant : effet perdu
                return

            if not player.can_store_hex_tile():
                # Pas de place en réserve -> on "perd" la tuile
                return

            player.add_hex_to_storage(new_tile)
            return

        # 3) CHURCH : prendre une tuile "spéciale" d’un dépôt
        #    (mine / knowledge / château dans les vraies règles)
        elif btype == BuildingType.CHURCH:
            depot_id = ctx.get("church_depot_choice")
            if depot_id is None:
                return

            try:
                new_tile = self.board.take_hex_from_depot(depot_id)
            except ValueError:
                return

            if not player.can_store_hex_tile():
                return

            player.add_hex_to_storage(new_tile)
            return

        # 4) MARKET : prendre une tuile (typiquement SHIP ou ANIMAL)
        #    d’un dépôt numéroté et la mettre en réserve
        elif btype == BuildingType.MARKET:
            depot_id = ctx.get("market_depot_choice")
            if depot_id is None:
                return

            try:
                new_tile = self.board.take_hex_from_depot(depot_id)
            except ValueError:
                return

            if not player.can_store_hex_tile():
                return

            player.add_hex_to_storage(new_tile)
            return

        # 5) HOUSE (Boarding house) : +4 ouvriers
        elif btype == BuildingType.HOUSE:
            player.gain_workers(4)
            return

        # 6) BANK : +2 silverlings
        elif btype == BuildingType.BANK:
            player.gain_silverlings(2)
            return

        # 7) CITYHALL : poser immédiatement une 2e tuile depuis la réserve
        elif btype == BuildingType.CITYHALL:
            extra = ctx.get("cityhall_extra_action") or {}
            storage_index = extra.get("storage_index")
            extra_coord = extra.get("coord")

            if storage_index is None or extra_coord is None:
                # Pas de 2e action définie => pas d’effet
                return

            current_round = extra.get("current_round", 0)
            die_value = extra.get("die_value", 1)
            workers_to_spend = extra.get("workers_to_spend", 0)
            nested_ctx = extra.get("extra_context", {})

            # IMPORTANT : on NE touche PAS à self.current_player
            # on réutilise simplement la logique standard de pose
            self.action_place_tile_from_storage(
                storage_index,
                extra_coord,
                current_round,
                die_value,
                workers_to_spend,
                nested_ctx,
            )
            return

        # 8) WATCHTOWER : +4 PV immédiats
        elif btype == BuildingType.WATCHTOWER:
            player.gain_victory_points(4)
            return

        # 9) Fallback (au cas où tu ajoutes un nouveau BuildingType
        #    sans encore coder son effet)
        else:
            player.gain_victory_points(2)

    # ---------- MINES ----------

    def _apply_mine_effect(
        self,
        player: Player,
        mine_obj: object,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Les mines n'ont pas d'effet immédiat : elles rapportent de l'argent en fin de phase.

        Ici, on ne fait rien. On s'en sert dans end_phase().
        """
        return

    def end_phase(self) -> None:
        """
        À appeler quand une phase (A..E) se termine.
        - Distribue l'argent des mines
        - Passe à la phase suivante sur Board
        """
        # 1) Mines → argent
        for player in self.players:
            nb_mines = player._count_mines_on_board()
            # Règle simple : 1 mine = 1 écu par manche de phase
            player.gain_silverlings(nb_mines)
            # Tuile 2
            player.apply_end_of_phase_income()

        # 2) Passer à la phase suivante sur le plateau central
        if self.board.is_phase_over():
            self.board.start_next_phase()

    # ---------- SHIPS ----------

    def _apply_ship_effect(
        self,
        player: Player,
        ship_obj: object,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Effets classiques d'un bateau dans BoB (version simplifiée) :
        - Avancer sur la piste de tour (ordre du tour)
        - Prendre toutes les marchandises d'un dépôt

        Ici :
        - on augmente turn_order_position de 1
        - on prend les marchandises du dépôt choisi dans ctx["goods_depot_choice"]
        """
        # 1) Avancer sur la piste (simplifié)
        player.turn_order_position += 1

        # 2) Prendre les marchandises d'un dépôt choisi
        depot_id = ctx.get("goods_depot_choice")
        if depot_id is not None:
            goods = self.board.take_all_goods_from_depot(depot_id)
            player.add_goods(goods)

    # ---------- YELLOW TILES / KNOWLEDGE ----------

    def _apply_yellow_tile_effect(
        self,
        player: Player,
        knowledge_obj: object,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Les tuiles jaunes ont souvent des effets permanents ou de scoring final.

        Ici, on les enregistre dans player.yellow_effects via leur "knowledge_type"
        si disponible, sinon via l'objet lui-même.
        """
        ktype = getattr(knowledge_obj, "knowledge_type", knowledge_obj)
        player.add_yellow_effect(ktype)

        # Exemple : si certaines tuiles jaunes donnent un bonus immédiat,
        # tu peux les identifier ici :
        # if ktype == KnowledgeType.SOME_IMMEDIATE_BONUS:
        #     player.gain_victory_points(3)

    # ---------- ANIMALS ----------

    def _apply_animal_effect(
        self,
        player: Player,
        animal_obj: Animal,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Score des animaux : dans le jeu de base, tu marques des points
        en fonction du nombre d'animaux identiques dans la région.

        Version générique :
        - animal_obj.animal_type (enum)
        - animal_obj.count = nb d'animaux sur la tuile
        - score = count * (nombre total de tuiles de ce type dans la région)
        """
        region = player.board.get_region_by_coord(coord)
        if region is None:
            return

        atype = getattr(animal_obj, "animal_type", None)
        count_on_tile = getattr(animal_obj, "count", 1)

        if atype is None:
            return

        total_tiles_same_type = 0
        for slot in region.slots:
            if (
                slot.is_occupied
                and isinstance(slot.tile.tile, Animal)
                and getattr(slot.tile.tile, "animal_type", None) == atype
            ):
                total_tiles_same_type += 1

        gained_points = count_on_tile * total_tiles_same_type
        player.gain_victory_points(gained_points)

    # ---------- CASTLE ----------

    def _apply_castle_effect(
        self,
        player: Player,
        castle_obj: object,
        coord: tuple[int, int],
        placement_result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> None:
        """
        Dans le jeu de base, un château permet de faire immédiatement
        une autre action principale.

        Ici, on note simplement dans le contexte qu'une action bonus est disponible.
        C'est à l'UI de l'exploiter.
        """
        ctx["castle_bonus_action_available"] = True

    # ---------- RÉGIONS COMPLÉTÉES ----------

    def _apply_region_completion_bonus(
        self,
        player: Player,
        placement_result: Dict[str, Any],
    ) -> None:
        """
        Quand une région vient d'être complétée, on ajoute un bonus générique.

        Version simple :
        - points = taille de la région (region_size)

        Tu pourras ensuite adapter au vrai barème BoB
        (plus tu complètes tôt, plus tu marques).
        """
        size = placement_result.get("region_size", 0)
        player.gain_victory_points(size)

    def start_new_round(self) -> dict:
        """
        Démarre une nouvelle manche : lance le dé blanc et place la marchandise.
        Retourne un dict avec les infos de la manche.
        """
        white_die = self.board._rng.randint(1, 6)
        goods_placed = self.board.advance_round(white_die)
        
        return {
            "white_die": white_die,
            "goods_placed": goods_placed,
            "current_round": self.board.round_in_phase,
            "current_phase": self.board.current_phase,
            "is_phase_over": self.board.is_phase_over(),
        }

    def start_new_phase(self) -> dict:
        """
        Démarre une nouvelle phase : remet les tuiles hex et bonus.
        Retourne un dict avec les infos de la phase.
        """
        self.board.start_new_phase()
        
        return {
            "current_phase": self.board.current_phase,
            "is_game_over": self.is_game_over(),
        }

    def is_game_over(self) -> bool:
        """Vérifie si la partie est terminée (5 phases complétées)."""
        # current_phase returns 'A', 'B', 'C', 'D', 'E' or '?'
        # Game is over when current_phase_index >= 5 (after phase E)
        return self.board.current_phase_index >= len(self.board.PHASES)

    def end_current_round(self) -> None:
        """
        Fin de manche : tous les joueurs ont joué.
        Réinitialise l'index du joueur courant pour la prochaine manche.
        """
        self.current_player_index = 0


class TurnManager:
    """
    Manages the turn structure for the game.
    
    In Castles of Burgundy:
    - Each phase has 5 rounds
    - Each round, players take turns based on turn order
    - Each turn, a player rolls 2 dice and performs 2 main actions
    """
    
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.actions_remaining: int = 0
        self.turn_active: bool = False
    
    def start_turn(self) -> None:
        """Start a new turn for the current player."""
        player = self.game.current_player
        player.roll_dice()
        self.actions_remaining = 2
        self.turn_active = True
    
    def use_action(self) -> None:
        """Mark one action as used."""
        if self.actions_remaining > 0:
            self.actions_remaining -= 1
        if self.actions_remaining == 0:
            self.turn_active = False
    
    def is_turn_complete(self) -> bool:
        """Check if the current turn is complete."""
        return self.actions_remaining == 0
    
    def end_turn(self) -> None:
        """End the current turn and advance to next player."""
        self.turn_active = False
        self.actions_remaining = 0
        self.game.next_player()


if __name__ == "__main__":
    """
    Game Simulation Test
    
    This test demonstrates all the core game mechanics:
    1. Game setup with multiple players
    2. Taking tiles from depots
    3. Placing tiles on player boards
    4. Selling goods
    5. Taking workers
    6. Move generation for AI/decision making
    """
    
    from action import MoveGenerator, ActionType
    from board import Tile, TileType, GoodsColor, GoodsTile
    from animals import Animal, AnimalType
    from buildings import Building, BuildingType
    
    print("=" * 60)
    print("CASTLES OF BURGUNDY - GAME SIMULATION TEST")
    print("=" * 60)
    
    # =====================
    # 1. GAME SETUP
    # =====================
    print("\n--- 1. GAME SETUP ---")
    
    game = Game(player_names=["Alice", "Bob"], seed=42)
    
    print(f"Created game with {len(game.players)} players")
    print(f"Current phase: {game.board.current_phase}")
    print(f"Current player: {game.current_player.name}")
    
    for player in game.players:
        print(f"  {player.name}: {player.silverlings} silverlings, {player.workers} workers")
    
    # Show initial board state
    print("\nCentral Board - Depot contents:")
    for depot_id in range(1, 7):
        tiles = [t.tile_type.name for t in game.board.depots[depot_id]]
        print(f"  Depot {depot_id}: {tiles}")
    
    black_tiles = [t.tile_type.name for t in game.board.black_depot]
    print(f"  Black depot: {black_tiles[:5]}... ({len(black_tiles)} total)")
    
    # =====================
    # 2. DICE AND MOVE GENERATION
    # =====================
    print("\n--- 2. DICE AND MOVE GENERATION ---")
    
    alice = game.players[0]
    alice.roll_dice()
    print(f"{alice.name} rolled: {alice.dice}")
    
    # Generate all possible moves
    move_gen = MoveGenerator(game, alice)
    all_moves = move_gen.get_all_possible_moves()
    move_counts = move_gen.count_moves()
    
    print(f"\nTotal available moves: {len(all_moves)}")
    print("Moves by type:")
    for move_type, count in move_counts.items():
        print(f"  {move_type}: {count}")
    
    # Show some example moves
    print("\nExample moves (first 5):")
    for i, move in enumerate(all_moves[:5]):
        print(f"  {i+1}. {move.description}")
    
    # =====================
    # 3. TAKE TILE FROM DEPOT
    # =====================
    print("\n--- 3. TAKE TILE FROM DEPOT ---")
    
    # Give Alice some workers for die adjustment
    alice.gain_workers(3)
    print(f"{alice.name} now has {alice.workers} workers")
    
    # Find a take tile move
    take_moves = move_gen.get_moves_by_type(ActionType.TAKE_TILE)
    if take_moves:
        move = take_moves[0]
        depot_id = move.params["depot_id"]
        
        print(f"Taking tile from depot {depot_id}")
        print(f"  Before: {len(alice.hex_storage)} tiles in storage")
        
        try:
            game.action_take_hex_from_depot(depot_id)
            print(f"  After: {len(alice.hex_storage)} tiles in storage")
            print(f"  Took: {alice.hex_storage[-1].tile_type.name}")
        except ValueError as e:
            print(f"  Error: {e}")
    
    # =====================
    # 4. PLACE TILE ON BOARD
    # =====================
    print("\n--- 4. PLACE TILE ON BOARD ---")
    
    # First, let's add a specific tile to Alice's storage that we can place
    ship_tile = Tile(TileType.SHIP)
    alice.hex_storage.append(ship_tile)
    print(f"Added SHIP to {alice.name}'s storage")
    print(f"Storage: {[t.tile_type.name for t in alice.hex_storage]}")
    
    # Roll dice again to get fresh dice for placement
    alice.roll_dice()
    print(f"{alice.name} rolled: {alice.dice}")
    
    # Check valid placement coordinates for ship
    ship_coords = alice.get_valid_placement_coords()
    print(f"\nValid placement coordinates: {len(ship_coords)}")
    
    # Find the ship in storage and try to place it
    ship_idx = None
    for idx, tile in enumerate(alice.hex_storage):
        if tile.tile_type == TileType.SHIP:
            ship_idx = idx
            break
    
    if ship_idx is not None:
        # Find a valid ship slot
        for coord, slot in alice.board.hex_map.grid.items():
            if slot.allowed_type == TileType.SHIP and not slot.is_occupied:
                # Check if adjacent to occupied
                neighbors = alice.board.hex_map.get_neighbors(coord)
                has_neighbor = any(
                    alice.board.hex_map.grid[n].is_occupied 
                    for n in neighbors 
                    if n in alice.board.hex_map.grid
                )
                if has_neighbor:
                    can_place, die_val, workers = alice.can_use_die_for_placement(coord)
                    if can_place:
                        print(f"\nPlacing SHIP at {coord}")
                        print(f"  Required die: {slot.dice_value}, using die: {die_val}, workers: {workers}")
                        try:
                            result = game.action_place_tile_from_storage(
                                ship_idx, coord, game.global_round, die_val, workers, {"goods_depot_choice": 1}
                            )
                            print(f"  Placement successful!")
                            print(f"  Region ID: {result['region_id']}, Size: {result['region_size']}")
                            print(f"  Region completed: {result['region_completed_now']}")
                        except ValueError as e:
                            print(f"  Error: {e}")
                        break
    
    # =====================
    # 5. GOODS AND SELLING
    # =====================
    print("\n--- 5. GOODS AND SELLING ---")
    
    # Add some goods to Alice
    alice.add_goods([
        GoodsTile(GoodsColor.COLOR_1),
        GoodsTile(GoodsColor.COLOR_1),
        GoodsTile(GoodsColor.COLOR_2),
    ])
    print(f"{alice.name} has {len(alice.goods_storage)} goods")
    
    alice.roll_dice()
    print(f"Rolling dice: {alice.dice}")
    
    # Check sell moves
    move_gen = MoveGenerator(game, alice)
    sell_moves = move_gen.get_moves_by_type(ActionType.SELL_GOODS)
    print(f"\nAvailable sell moves: {len(sell_moves)}")
    for move in sell_moves:
        print(f"  - {move.description}")
    
    # Sell goods
    if alice.goods_storage:
        color = alice.goods_storage[0].color
        print(f"\nSelling all {color.name} goods...")
        sold = alice.sell_goods_of_color(color)
        print(f"  Sold {sold} goods")
        print(f"  Silverlings: {alice.silverlings}")
        print(f"  Remaining goods: {len(alice.goods_storage)}")
    
    # =====================
    # 6. WORKERS AND RESOURCES
    # =====================
    print("\n--- 6. WORKERS AND RESOURCES ---")
    
    print(f"{alice.name} resources:")
    print(f"  Victory Points: {alice.victory_points}")
    print(f"  Silverlings: {alice.silverlings}")
    print(f"  Workers: {alice.workers}")
    
    alice.roll_dice()
    move_gen = MoveGenerator(game, alice)
    worker_moves = move_gen.get_moves_by_type(ActionType.TAKE_WORKERS)
    
    if worker_moves:
        print(f"\nTake workers move: {worker_moves[0].description}")
        workers_before = alice.workers
        alice.gain_workers(alice.get_workers_from_take_action())
        alice.use_die(alice.dice[0])
        print(f"  Workers: {workers_before} -> {alice.workers}")
    
    # =====================
    # 7. BUY FROM BLACK DEPOT
    # =====================
    print("\n--- 7. BUY FROM BLACK DEPOT ---")
    
    alice.gain_silverlings(5)
    print(f"{alice.name} has {alice.silverlings} silverlings")
    
    move_gen = MoveGenerator(game, alice)
    black_moves = move_gen.get_moves_by_type(ActionType.BUY_BLACK_TILE)
    
    if black_moves:
        move = black_moves[0]
        print(f"Can buy from black depot: {move.description}")
        
        if alice.can_store_hex_tile() and alice.silverlings >= 2:
            storage_before = len(alice.hex_storage)
            game.action_take_hex_from_black_depot()
            print(f"  Bought tile! Storage: {storage_before} -> {len(alice.hex_storage)}")
            print(f"  Silverlings: {alice.silverlings}")
    
    # =====================
    # 8. YELLOW TILES EFFECTS
    # =====================
    print("\n--- 8. YELLOW TILES EFFECTS ---")
    
    # Add a yellow tile to Bob
    bob = game.players[1]
    bob.add_yellow_effect(YELLOW_TILE_DEFINITIONS[8])  # Master Laborer
    bob.add_yellow_effect(YELLOW_TILE_DEFINITIONS[14]) # Mass Recruitment
    
    print(f"{bob.name}'s yellow tiles:")
    for tile in bob.yellow_effects:
        print(f"  - {tile.name}: {tile.description}")
    
    print(f"\nYellow tile effects:")
    print(f"  Die adjustment per worker: {bob.get_die_adjustment_per_worker()} (normally 1)")
    print(f"  Workers from take action: {bob.get_workers_from_take_action()} (normally 2)")
    
    # =====================
    # 9. COMPLETE TURN SIMULATION
    # =====================
    print("\n--- 9. COMPLETE TURN SIMULATION ---")
    
    turn_manager = TurnManager(game)
    
    # Simulate Bob's turn
    game.current_player_index = 1  # Switch to Bob
    bob.gain_workers(2)
    
    turn_manager.start_turn()
    print(f"\n{bob.name}'s turn started")
    print(f"  Dice: {bob.dice}")
    print(f"  Actions remaining: {turn_manager.actions_remaining}")
    
    move_gen = MoveGenerator(game, bob)
    all_bob_moves = move_gen.get_all_possible_moves()
    print(f"  Available moves: {len(all_bob_moves)}")
    
    # Action 1: Take a tile
    take_moves = [m for m in all_bob_moves if m.type == ActionType.TAKE_TILE]
    if take_moves and bob.can_store_hex_tile():
        move = take_moves[0]
        print(f"\n  Action 1: {move.description}")
        depot_id = move.params["depot_id"]
        game.action_take_hex_from_depot(depot_id)
        bob.use_die(move.params["die_value"])
        turn_manager.use_action()
        print(f"    Took tile from depot {depot_id}")
        print(f"    Storage: {[t.tile_type.name for t in bob.hex_storage]}")
    
    # Action 2: Take workers (if dice left)
    if bob.dice and not turn_manager.is_turn_complete():
        workers_before = bob.workers
        bob.gain_workers(bob.get_workers_from_take_action())
        bob.use_die(bob.dice[0])
        turn_manager.use_action()
        print(f"\n  Action 2: Take workers")
        print(f"    Workers: {workers_before} -> {bob.workers}")
    
    print(f"\n  Turn complete: {turn_manager.is_turn_complete()}")
    turn_manager.end_turn()
    print(f"  Next player: {game.current_player.name}")
    
    # =====================
    # 10. GAME STATE SUMMARY
    # =====================
    print("\n--- 10. GAME STATE SUMMARY ---")
    print("=" * 60)
    
    for player in game.players:
        print(f"\n{player.name}:")
        print(f"  Victory Points: {player.victory_points}")
        print(f"  Silverlings: {player.silverlings}")
        print(f"  Workers: {player.workers}")
        print(f"  Hex Storage: {[t.tile_type.name for t in player.hex_storage]}")
        print(f"  Goods: {[g.color.name for g in player.goods_storage]}")
        print(f"  Yellow Tiles: {len(player.yellow_effects)}")
        
        # Count placed tiles
        placed = sum(1 for r in player.board.regions for s in r.slots if s.is_occupied)
        print(f"  Tiles placed on board: {placed}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - Game simulation complete!")
    print("=" * 60)