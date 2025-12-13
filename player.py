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

        Renvoie le nombre de marchandises vendues (pour calculer PV, argent, etc.).
        """
        remaining: List[GoodsTile] = []
        sold = 0
        for g in self.goods_storage:
            if g.color == color:
                sold += 1
            else:
                remaining.append(g)
        self.goods_storage = remaining
        return sold

    # =============================
    # Tuiles jaunes (knowledge tiles)
    # =============================

    def add_yellow_effect(self, effect: "YellowTile") -> None:
        """
        Ajoute un effet de tuile jaune (KnowledgeType par ex.) au set.
        """
        self.yellow_effects.add(effect)

    def has_yellow_effect(self, effect: "YellowTile") -> bool:
        """
        Vérifie si le joueur possède un effet jaune donné.
        """
        return effect in self.yellow_effects
