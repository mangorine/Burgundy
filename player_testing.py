from dataclasses import dataclass, field
from typing import List, Set, Optional

# On suppose que ce fichier est dans le même module que ton code,
# donc Tile, GoodsTile, PlayerBoard, TileType sont déjà définis plus haut
# ou importés depuis ton module "boards".

# from boards import Tile, GoodsTile, PlayerBoard  # si séparé
from animals import Animal, AnimalType
from buildings import (
    Building,
    BuildingType,
)  # + éventuellement Knowledge, KnowledgeType


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
    layout_id: int
    board: "PlayerBoard" = field(init=False)

    silverlings: int = 0
    workers: int = 0
    victory_points: int = 0

    # Tuiles hex prises mais pas encore posées.
    hex_storage: List["Tile"] = field(default_factory=list)
    # Marchandises stockées chez le joueur.
    goods_storage: List["GoodsTile"] = field(default_factory=list)

    # Effets des tuiles jaunes (KnowledgeType ou équivalent)
    yellow_effects: Set[object] = field(default_factory=set)

    # Pour éventuellement gérer l’ordre du tour / piste de navigation
    turn_order_position: int = 0

    def __post_init__(self) -> None:
        """
        Initialise le PlayerBoard après la création du Player.
        Complexité : O(N) où N = nombre de cases du PlayerBoard.
        """
        self.board = PlayerBoard(self.layout_id)

    # =============================
    # Gestion des ressources simples
    # =============================

    def gain_victory_points(self, amount: int) -> None:
        """
        Ajoute des points de victoire au joueur.
        Complexité : O(1).
        """
        self.victory_points += amount

    def gain_silverlings(self, amount: int) -> None:
        """
        Ajoute des écus.
        Complexité : O(1).
        """
        self.silverlings += amount

    def spend_silverlings(self, amount: int) -> None:
        """
        Dépense des écus, lève une erreur si pas assez.
        Complexité : O(1).
        """
        if self.silverlings < amount:
            raise ValueError(f"{self.name} n'a pas assez d'écus.")
        self.silverlings -= amount

    def gain_workers(self, amount: int) -> None:
        """
        Ajoute des ouvriers.
        Complexité : O(1).
        """
        self.workers += amount

    def spend_workers(self, amount: int) -> None:
        """
        Dépense des ouvriers, lève une erreur si pas assez.
        Complexité : O(1).
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
        Complexité : O(1).
        """
        return len(self.hex_storage) < 3

    def add_hex_to_storage(self, tile: "Tile") -> None:
        """
        Ajoute une tuile hex à la réserve du joueur.
        Complexité : O(1) amorti (append).
        """
        if not self.can_store_hex_tile():
            raise ValueError(f"{self.name} ne peut pas stocker plus de tuiles.")
        self.hex_storage.append(tile)

    def remove_hex_from_storage(self, index: int) -> "Tile":
        """
        Retire une tuile hex de la réserve, par index (0,1,2).

        Complexité : O(1) pour pop sur liste.
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
        Complexité : O(k) pour k marchandises ajoutées.
        """
        self.goods_storage.extend(goods)

    def sell_goods_of_color(self, color: "GoodsColor") -> int:
        """
        Vend toutes les marchandises d'une couleur donnée.

        Renvoie le nombre de marchandises vendues (pour calculer PV, argent, etc.).

        Complexité : O(n) sur n marchandises en stock.
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

    def add_yellow_effect(self, effect: object) -> None:
        """
        Ajoute un effet de tuile jaune (KnowledgeType par ex.) au set.

        Complexité : O(1) en moyenne (set.add).
        """
        self.yellow_effects.add(effect)

    def has_yellow_effect(self, effect: object) -> bool:
        """
        Vérifie si le joueur possède un effet jaune donné.
        Complexité : O(1) en moyenne.
        """
        return effect in self.yellow_effects
