from dataclasses import dataclass, field
from typing import List, Set, TYPE_CHECKING
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
