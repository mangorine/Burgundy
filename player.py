from dataclasses import dataclass, field
from typing import List, Set, Tuple, TYPE_CHECKING
from board import PlayerBoard, Tile, GoodsTile, TileType, GoodsColor
from animals import Animal, AnimalType
from buildings import Building, BuildingType

if TYPE_CHECKING:
    from yellow_tiles import YellowTile


@dataclass
class Player:
    """
    Représente un joueur complet.

    Il possède :
    - un PlayerBoard (plateau perso)
    - des ressources (argent, ouvriers, PV)
    - une réserve de tuiles hex (3 emplacements dans le jeu de base)
    - des marchandises
    - des effets de tuiles jaunes (knowledge tiles)

    Toutes les opérations ici sont en O(1) ou O(n) sur la taille des listes
    (n = nb de tuiles ou marchandises).
    """

    name: str
    layout_id: int = 1
    board: "PlayerBoard" = field(init=False)

    silverlings: int = 0
    workers: int = 0
    victory_points: int = 0

    # Tuiles hex prises mais pas encore posées.
    hex_storage: List["Tile"] = field(default_factory=list)
    # Marchandises stockées chez le joueur.
    goods_storage: List["GoodsTile"] = field(default_factory=list)

    # Effets des tuiles jaunes (YellowTile objects: Income, RuleModification, or Scoring)
    yellow_effects: Set["YellowTile"] = field(default_factory=set)

    # Track sold goods for end-game scoring
    sold_goods_types: Set["GoodsColor"] = field(default_factory=set)
    total_goods_sold: int = 0
    
    # Track bonus tiles claimed
    bonus_tiles: List[str] = field(default_factory=list)

    # Pour éventuellement gérer l’ordre du tour / piste de navigation
    turn_order_position: int = 0

    # Dés pour les actions
    dice: List[int] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """
        Initialise le PlayerBoard après la création du Player.
        """
        self.board = PlayerBoard(self.layout_id)

    # =============================
    # Gestion des ressources simples
    # =============================

    def gain_victory_points(self, amount: int) -> None:
        """
        Ajoute des points de victoire au joueur.
        """
        self.victory_points += amount

    def gain_silverlings(self, amount: int) -> None:
        """
        Ajoute des écus.
        """
        self.silverlings += amount

    def spend_silverlings(self, amount: int) -> None:
        """
        Dépense des écus, lève une erreur si pas assez.
        """
        if self.silverlings < amount:
            raise ValueError(f"{self.name} n'a pas assez d'écus.")
        self.silverlings -= amount

    def gain_workers(self, amount: int) -> None:
        """
        Ajoute des ouvriers.
        """
        self.workers += amount

    def spend_workers(self, amount: int) -> None:
        """
        Dépense des ouvriers, lève une erreur si pas assez.
        """
        if self.workers < amount:
            raise ValueError(f"{self.name} n'a pas assez d'ouvriers.")
        self.workers -= amount

    # =============================
    # Réserve de tuiles hex
    # =============================

    def can_store_hex_tile(self) -> bool:
        """
        Vérifie si le joueur peut encore stocker une tuile hex.

        Dans le jeu de base : 3 emplacements.
        """
        return len(self.hex_storage) < 3

    def add_hex_to_storage(self, tile: "Tile") -> None:
        """
        Ajoute une tuile hex à la réserve du joueur.
        """
        if not self.can_store_hex_tile():
            raise ValueError(f"{self.name} ne peut pas stocker plus de tuiles.")
        self.hex_storage.append(tile)

    def remove_hex_from_storage(self, index: int) -> "Tile":
        """
        Retire une tuile hex de la réserve, par index (0,1,2).
        """
        if not (0 <= index < len(self.hex_storage)):
            raise IndexError("Index de stockage invalide.")
        return self.hex_storage.pop(index)

    # =============================
    # Marchandises
    # =============================

    def add_goods(self, goods: List["GoodsTile"]) -> None:
        """
        Ajoute des marchandises à la réserve du joueur.
        """
        self.goods_storage.extend(goods)

    def sell_goods_of_color(self, color: "GoodsColor") -> int:
        """
        Vend toutes les marchandises d'une couleur donnée.
        Ajoute les VP et les silverlings avec les effets des tuiles jaunes si tuile jaune
        """
        remaining: List[GoodsTile] = []
        sold = 0
        for g in self.goods_storage:
            if g.color == color:
                sold += 1
            else:
                remaining.append(g)
        self.goods_storage = remaining
        
        if sold > 0:
            self.sold_goods_types.add(color)
            self.total_goods_sold += sold
            
            # Si tuile jaune 3 : 2 silver au lieu de 1
            silverlings_per_good = self.get_silverlings_per_good_sold()
            self.gain_silverlings(silverlings_per_good * sold)
            
            # Si tuile 4 : gagne 1 ouvrier en vendant des marchandises
            self.apply_goods_sold_effects(sold)
        
        return sold

    # =============================
    # Tuiles jaunes (knowledge tiles)
    # =============================

    def add_yellow_effect(self, effect: "YellowTile") -> None:
        """
        Ajoute un effet de tuile jaune (KnowledgeType par ex.) au set.
        """
        self.yellow_effects.add(effect)

    
    def has_yellow_tile_by_id(self, tile_id: int) -> bool:
        """
        Check si le joueur possède une tuile jaune avec id
        """
        for effect in self.yellow_effects:
            if effect.tile_id == tile_id:
                return True
        return False
    
    # =============================
    # Yellow Tile Rule Modifications
    # =============================

    # Tuile 1
    def allows_duplicate_buildings_in_city(self) -> bool:
        """
        Peut poser plusieurs bâtiments du même type dans une même ville si on a la tuile jaune 1.
        """
        return self.has_yellow_tile_by_id(1)
    
    # Tuile 3
    def get_silverlings_per_good_sold(self) -> int:
        """
        Tuile 3 (Master Merchant): 2 silverlings par marchandise vendue au lieu de 1.
        
        Donne 2 silverlings par marchandise vendue si on a la tuile jaune 3.
        """
        if self.has_yellow_tile_by_id(3):
            return 2
        return 1
    
    # Tuile 5
    def get_ship_goods_bonus(self) -> int:
        """
        Tuile 5 (Advanced Shipping): Prendre des marchandises de deux espaces voisins au lieu d'un.
        """
        if self.has_yellow_tile_by_id(5):
            return 2
        return 1
    
    # Tuile 6
    def can_access_black_depot(self) -> bool:
        """
        True si on a accès au black market
        """
        return self.has_yellow_tile_by_id(6)
    
    # Tuile 7
    def get_animal_placement_vp_bonus(self) -> int:
        """
        Donne un vp bonus par animal placé si on a la tuile jaune 7.
        """
        if self.has_yellow_tile_by_id(7):
            return 1
        return 0
    
    # Tuile 8
    def get_die_adjustment_per_worker(self) -> int:
        """
        Si on a la tuile jaune 8 (Master Laborer), on peut ajuster le dé de +/-2 par ouvrier.
        Sinon, c'est +/-1 par ouvrier.
        A appeler lorsque l'on veut changer la valeur d'un dé avec les ouvriers.
        """
        if self.has_yellow_tile_by_id(8):
            return 2
        return 1
    
    # Tuile 9 - 11
    def get_free_placement_die_adjustment(self, tile_type: TileType) -> bool:
        """
        Tuiles 9 - 11
        Ajustement de dé gratuit pour placement de tuiles hex spécifiques.
        
        Dispatch selon le type de tuile
        A appeler lors du placement des tuiles pour savoir si on peut ajuster le dé.
        """
        # Tile #9: Buildings
        if tile_type == TileType.BUILDING and self.has_yellow_tile_by_id(9):
            return True
        
        # Tile #10: Ships or Animals
        if (tile_type == TileType.SHIP or tile_type == TileType.ANIMAL) and self.has_yellow_tile_by_id(10):
            return True
        
        # Tile #11: Castles, Mines, or Knowledge
        if (tile_type == TileType.CASTLE or tile_type == TileType.MINE or 
            tile_type == TileType.KNOWLEDGE) and self.has_yellow_tile_by_id(11):
            return True
        
        return False
    
    # Tuile 12
    def can_take_from_depot_with_adjustment(self) -> bool:
        """
        Tuile 12 
        Permet de prendre des marchandises du dépôt avec un ajustement de dé.
        
        A appeler lors de la prise de marchandises du dépôt.
        """
        return self.has_yellow_tile_by_id(12)
    
    # Tuile 13
    def get_silverling_bonus_on_take_workers(self) -> int:
        """
        Donne 1 silver quand on prend un ouvrier
        """
        if self.has_yellow_tile_by_id(13):
            return 1
        return 0
    
    # Tuile 14
    def get_workers_from_take_action(self) -> int:
        """
        Prends 4 workers au lieu de 2 lorsque l'on fait "Take worker chips"
        """
        if self.has_yellow_tile_by_id(14):
            return 4
        return 2
    
    # =============================
    # Income Tiles (Phase-based)
    # =============================
    
    # Tuile 2
    def apply_end_of_phase_income(self) -> None:
        """
        A la fin de la phase, on gagne 1 worker par mine en plus des silvers
        """
        if self.has_yellow_tile_by_id(2):
            num_mines = self._count_mines_on_board()
            if num_mines > 0:
                self.gain_workers(num_mines)
    
    def _count_mines_on_board(self) -> int:
        """Count the number of mine tiles on the player's board."""
        count = 0
        for region in self.board.regions:
            for slot in region.slots:
                if slot.tile and slot.tile.tile_type == TileType.MINE:
                    count += 1
        return count
    
    # Tuile 4
    def apply_goods_sold_effects(self) -> None:
        """
        Ajoute 1 worker dès qu'on vend des marchandises si on a la tuile jaune 4.
        """
        if self.has_yellow_tile_by_id(4):
            self.gain_workers(1)
    
    # =============================
    # End-Game Scoring
    # =============================
    
    def calculate_yellow_tiles_score(self) -> int:
        """
        Calculate total victory points from all scoring yellow tiles.
        Call this at the end of the game.
        """
        from yellow_tiles import Scoring
        total_vp = 0
        for tile in self.yellow_effects:
            if isinstance(tile, Scoring):
                total_vp += tile.calculate_vp_end_of_game(self)
        return total_vp
    
    def add_bonus_tile(self, bonus_name: str) -> None:
        """
        Track a bonus tile claimed by the player (for end-game scoring).
        """
        self.bonus_tiles.append(bonus_name)

    # =============================
    # Dice Management
    # =============================

    def roll_dice(self) -> None:
        """
        Roll 2 dice at the beginning of the player's turn.
        Each die has values 1-6.
        """
        import random
        self.dice = [random.randint(1, 6), random.randint(1, 6)]

    def get_available_dice(self) -> List[int]:
        """
        Returns the list of dice values currently available to the player.
        """
        return self.dice.copy()

    def has_die_value(self, value: int) -> bool:
        """
        Check if the player has a die with the specified value.
        """
        return value in self.dice

    def use_die(self, value: int) -> None:
        """
        Remove a die with the specified value from the player's available dice.
        Raises ValueError if no such die exists.
        """
        if value not in self.dice:
            raise ValueError(f"{self.name} does not have a die with value {value}.")
        self.dice.remove(value)

    def can_reach_value_with_workers(self, target: int, base_value: int) -> Tuple[bool, int]:
        """
        Check if the player can adjust a die from base_value to target using workers.
        Returns (can_reach, workers_needed).
        
        Workers can adjust die value by +/- adjustment_per_worker (typically 1, or 2 with yellow tile 8).
        Die values wrap around: 6+1=1, 1-1=6.
        """
        if target < 1 or target > 6 or base_value < 1 or base_value > 6:
            return (False, 0)
        
        if base_value == target:
            return (True, 0)
        
        adjustment = self.get_die_adjustment_per_worker()
        
        # Calculate forward distance (wrapping at 6->1)
        forward_dist = (target - base_value) % 6
        if forward_dist == 0:
            forward_dist = 6
            
        # Calculate backward distance (wrapping at 1->6)
        backward_dist = (base_value - target) % 6
        if backward_dist == 0:
            backward_dist = 6
        
        min_distance = min(forward_dist, backward_dist)
        workers_needed = (min_distance + adjustment - 1) // adjustment  # Ceiling division
        
        if workers_needed <= self.workers:
            return (True, workers_needed)
        return (False, workers_needed)

    def can_use_die_for_depot(self, depot_id: int) -> Tuple[bool, int, int]:
        """
        Check if the player can take a tile from a depot with the given ID.
        
        Returns: (can_take, die_value_to_use, workers_needed)
        - can_take: True if the action is possible
        - die_value_to_use: The die value that can be used (0 if not possible)
        - workers_needed: Number of workers needed (0 if exact match)
        """
        if depot_id < 1 or depot_id > 6:
            return (False, 0, 0)
        
        # First check for exact match
        if depot_id in self.dice:
            return (True, depot_id, 0)
        
        # Check if we can reach depot_id using workers
        best_option: Tuple[bool, int, int] = (False, 0, 999)
        for die_value in self.dice:
            can_reach, workers_needed = self.can_reach_value_with_workers(depot_id, die_value)
            if can_reach and workers_needed < best_option[2]:
                best_option = (True, die_value, workers_needed)
        
        if best_option[0]:
            return best_option
        return (False, 0, 0)

    def can_use_die_for_placement(self, coord: Tuple[int, int]) -> Tuple[bool, int, int]:
        """
        Check if the player can place a tile at the given coordinate.
        
        Returns: (can_place, die_value_to_use, workers_needed)
        - can_place: True if the action is possible with available dice
        - die_value_to_use: The die value that can be used (0 if not possible)
        - workers_needed: Number of workers needed (0 if exact match or free adjustment)
        """
        slot = self.board.hex_map.get_slot(coord)
        if slot is None:
            return (False, 0, 0)
        
        target_value = slot.dice_value
        tile_type = slot.allowed_type
        
        # Check for exact die match
        if target_value in self.dice:
            return (True, target_value, 0)
        
        # Check for free placement adjustment (yellow tiles 9-11)
        has_free_adjustment = self.get_free_placement_die_adjustment(tile_type)
        if has_free_adjustment and len(self.dice) > 0:
            # Can use any die with free adjustment
            return (True, self.dice[0], 0)
        
        # Check if we can reach target using workers
        best_option: Tuple[bool, int, int] = (False, 0, 999)
        for die_value in self.dice:
            can_reach, workers_needed = self.can_reach_value_with_workers(target_value, die_value)
            if can_reach and workers_needed < best_option[2]:
                best_option = (True, die_value, workers_needed)
        
        if best_option[0]:
            return best_option
        return (False, 0, 0)

    def can_perform_action_with_die(self, action_type: str, **kwargs) -> Tuple[bool, int, int]:
        """
        Generic check if an action can be performed with available dice.
        
        Parameters:
        - action_type: 'take_tile', 'place_tile', 'take_goods', 'sell_goods'
        - kwargs: Additional parameters depending on action type
          - depot_id: for 'take_tile' or 'take_goods'
          - coord: for 'place_tile'
        
        Returns: (can_perform, die_value_to_use, workers_needed)
        """
        if len(self.dice) == 0:
            return (False, 0, 0)
        
        if action_type == 'take_tile' or action_type == 'take_goods':
            depot_id = kwargs.get('depot_id')
            if depot_id is None:
                return (False, 0, 0)
            return self.can_use_die_for_depot(depot_id)
        
        elif action_type == 'place_tile':
            coord = kwargs.get('coord')
            if coord is None:
                return (False, 0, 0)
            return self.can_use_die_for_placement(coord)
        
        elif action_type == 'sell_goods':
            # Selling goods doesn't require a die, just having goods
            return (True, 0, 0)
        
        return (False, 0, 0)

    def get_valid_depot_ids(self) -> List[Tuple[int, int, int]]:
        """
        Get all depot IDs the player can access with current dice and workers.
        
        Returns: List of (depot_id, die_value_to_use, workers_needed) tuples
        """
        valid_depots = []
        for depot_id in range(1, 7):
            can_take, die_value, workers_needed = self.can_use_die_for_depot(depot_id)
            if can_take:
                valid_depots.append((depot_id, die_value, workers_needed))
        return valid_depots

    def get_valid_placement_coords(self) -> List[Tuple[Tuple[int, int], int, int]]:
        """
        Get all coordinates where the player can place tiles with current dice.
        
        Returns: List of (coord, die_value_to_use, workers_needed) tuples
        """
        valid_coords = []
        for coord, slot in self.board.hex_map.grid.items():
            if not slot.is_occupied:
                can_place, die_value, workers_needed = self.can_use_die_for_placement(coord)
                if can_place:
                    valid_coords.append((coord, die_value, workers_needed))
        return valid_coords
