from enum import Enum
from typing import Optional, Dict, List, Tuple, Set
import random
from animals import *
from buildings import *


class TileType(Enum):
    CASTLE = "castle"
    BUILDING = "building"
    SHIP = "ship"
    MINE = "mine"
    ANIMAL = "animal"
    KNOWLEDGE = "knowledge"


class Tile:
    def __init__(self, tile_type: TileType, is_black: bool = False):
        self.tile_type = tile_type
        self.is_black = is_black
        self.tile = None


class Slot:
    def __init__(self, coord: Tuple[int, int], allowed_type: TileType):
        self.coord = coord
        self.allowed_type = allowed_type
        self.is_occupied = False
        self.tile = None

    def can_place_tile(self, tile: Tile) -> bool:
        """Est ce qu'on peut placer une tuile ici ?"""
        return (not self.is_occupied) and (tile.tile_type == self.allowed_type)

    def place_tile(self, tile: Tile) -> None:
        """Place une tuile dans le slot"""
        if self.can_place_tile(tile):
            self.tile = tile
            self.is_occupied = True
        else:
            raise ValueError("Nope, cannot place tile here.")


class Region:
    def __init__(self, region_id: int, slots: List[Slot], allowed_type: TileType):
        self.region_id = region_id
        self.slots = slots[:]
        self.allowed_type = allowed_type
        self.has_scored = False

    def size(self) -> int:
        """Retourne la taille de la region"""
        return len(self.slots)

    def is_completed(self) -> bool:
        """Est ce que la region est complete"""
        for slot in self.slots:
            if not slot.is_occupied:
                return False
        return True

    def scored(self) -> None:
        """A appeler qd la region score pour pas qu'elle re rapporte
        des points"""
        self.has_scored = True


LAYOUTS = {
    1: {
        # r = -3 (q = 0..3)
        (0, -3): TileType.ANIMAL,
        (1, -3): TileType.CASTLE,
        (2, -3): TileType.CASTLE,
        (3, -3): TileType.KNOWLEDGE,
        # r = -2 (q = -1..3)
        (-1, -2): TileType.ANIMAL,
        (0, -2): TileType.ANIMAL,
        (1, -2): TileType.CASTLE,
        (2, -2): TileType.KNOWLEDGE,
        (3, -2): TileType.BUILDING,
        # r = -1 (q = -2..3)
        (-2, -1): TileType.ANIMAL,
        (-1, -1): TileType.ANIMAL,
        (0, -1): TileType.BUILDING,
        (1, -1): TileType.KNOWLEDGE,
        (2, -1): TileType.BUILDING,
        (3, -1): TileType.BUILDING,
        # r = 0 (q = -3..3)
        (-3, 0): TileType.SHIP,
        (-2, 0): TileType.SHIP,
        (-1, 0): TileType.SHIP,
        (0, 0): TileType.CASTLE,
        (1, 0): TileType.SHIP,
        (2, 0): TileType.SHIP,
        (3, 0): TileType.SHIP,
        # r = 1 (q = -3..2)
        (-3, 1): TileType.BUILDING,
        (-2, 1): TileType.BUILDING,
        (-1, 1): TileType.MINE,
        (0, 1): TileType.BUILDING,
        (1, 1): TileType.BUILDING,
        (2, 1): TileType.ANIMAL,
        # r = 2 (q = -3..1)
        (-3, 2): TileType.BUILDING,
        (-2, 2): TileType.MINE,
        (-1, 2): TileType.KNOWLEDGE,
        (0, 2): TileType.BUILDING,
        (1, 2): TileType.BUILDING,
        # r = 3 (q = -3..0)
        (-3, 3): TileType.MINE,
        (-2, 3): TileType.KNOWLEDGE,
        (-1, 3): TileType.KNOWLEDGE,
        (0, 3): TileType.BUILDING,
    },
    2: {
        # r = -3 (q = 0..3)
        (0, -3): TileType.SHIP,
        (1, -3): TileType.ANIMAL,
        (2, -3): TileType.ANIMAL,
        (3, -3): TileType.CASTLE,
        # r = -2 (q = -1..3)
        (-1, -2): TileType.SHIP,
        (0, -2): TileType.BUILDING,
        (1, -2): TileType.ANIMAL,
        (2, -2): TileType.KNOWLEDGE,
        (3, -2): TileType.BUILDING,
        # r = -1 (q = -2..3)
        (-2, -1): TileType.ANIMAL,
        (-1, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
        (1, -1): TileType.KNOWLEDGE,
        (2, -1): TileType.BUILDING,
        (3, -1): TileType.BUILDING,
        # r = 0 (q = -3..3)
        (-3, 0): TileType.ANIMAL,
        (-2, 0): TileType.BUILDING,
        (-1, 0): TileType.KNOWLEDGE,
        (0, 0): TileType.KNOWLEDGE,
        (1, 0): TileType.BUILDING,
        (2, 0): TileType.KNOWLEDGE,
        (3, 0): TileType.ANIMAL,
        # r = 1 (q = -3..2)
        (-3, 1): TileType.KNOWLEDGE,
        (-2, 1): TileType.BUILDING,
        (-1, 1): TileType.MINE,
        (0, 1): TileType.MINE,
        (1, 1): TileType.BUILDING,
        (2, 1): TileType.SHIP,
        # r = 2 (q = -3..1)
        (-3, 2): TileType.BUILDING,
        (-2, 2): TileType.MINE,
        (-1, 2): TileType.MINE,
        (0, 2): TileType.KNOWLEDGE,
        (1, 2): TileType.SHIP,
        # r = 3 (q = -3..0)
        (-3, 3): TileType.CASTLE,
        (-2, 3): TileType.SHIP,
        (-1, 3): TileType.SHIP,
        (0, 3): TileType.ANIMAL,
    },
    3: {
        # r = -3 (q = 0..3)
        (0, -3): TileType.KNOWLEDGE,
        (1, -3): TileType.KNOWLEDGE,
        (2, -3): TileType.ANIMAL,
        (3, -3): TileType.SHIP,
        # r = -2 (q = -1..3)
        (-1, -2): TileType.KNOWLEDGE,
        (0, -2): TileType.KNOWLEDGE,
        (1, -2): TileType.ANIMAL,
        (2, -2): TileType.SHIP,
        (3, -2): TileType.SHIP,
        # r = -1 (q = -2..3)
        (-2, -1): TileType.BUILDING,
        (-1, -1): TileType.MINE,
        (0, -1): TileType.KNOWLEDGE,
        (1, -1): TileType.SHIP,
        (2, -1): TileType.BUILDING,
        (3, -1): TileType.BUILDING,
        # r = 0 (q = -3..3)
        (-3, 0): TileType.BUILDING,
        (-2, 0): TileType.MINE,
        (-1, 0): TileType.BUILDING,
        (0, 0): TileType.CASTLE,
        (1, 0): TileType.KNOWLEDGE,
        (2, 0): TileType.BUILDING,
        (3, 0): TileType.BUILDING,
        # r = 1 (q = -3..2)
        (-3, 1): TileType.BUILDING,
        (-2, 1): TileType.MINE,
        (-1, 1): TileType.KNOWLEDGE,
        (0, 1): TileType.KNOWLEDGE,
        (1, 1): TileType.SHIP,
        (2, 1): TileType.ANIMAL,
        # r = 2 (q = -3..1)
        (-3, 2): TileType.ANIMAL,
        (-2, 2): TileType.ANIMAL,
        (-1, 2): TileType.MINE,
        (0, 2): TileType.MINE,
        (1, 2): TileType.KNOWLEDGE,
        # r = 3 (q = -3..0)
        (-3, 3): TileType.ANIMAL,
        (-2, 3): TileType.BUILDING,
        (-1, 3): TileType.BUILDING,
        (0, 3): TileType.CASTLE,
    },
}


class HexMap:
    def __init__(self, layout_id: int = 1):
        # Initialisation d'une grille vide pour une carte hexagonale
        #  celle du joueur
        self.grid: Dict[Tuple[int, int], Slot] = {}
        all_coords = []
        for q in range(-3, -3 + 1):
            for r in range(-3, -3 + 1):
                if -3 <= q + r <= 3:
                    all_coords.append((q, r))
        layout = LAYOUTS.get(layout_id, {})
        for coord in all_coords:
            if coord not in layout:
                raise ValueError(f"Layout {layout_id} is missing coordinate {coord}")
            else:
                allowed_type = layout[coord]
            self.grid[coord] = Slot(coord, allowed_type)

    def get_slot(self, coord: Tuple[int, int]) -> Optional[Slot]:
        """Retourne le slot a la coordonnee donnee"""
        if coord not in self.grid:
            raise ValueError(f"Coordinate {coord} is not in the grid")
        return self.grid[coord]

    def get_neighbors(self, coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Retourne les coordonnees des voisins d'une case"""
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        neighbors = []
        for direction in directions:
            neighbor = (coord[0] + direction[0], coord[1] + direction[1])
            if neighbor in self.grid:
                neighbors.append(neighbor)
        return neighbors

    def fill_region(self, start: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Retourne toutes les coordonnees d'une region a partir d'une coordonnee de depart"""
        if start not in self.grid:
            raise ValueError(f"Coordinate {start} is not in the grid")
        start_slot = self.grid[start]
        target_type = start_slot.allowed_type

        to_visit = [start]
        visited: Set[Tuple[int, int]] = set()
        region_coords: List[Tuple[int, int]] = []

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            current_slot = self.grid[current]
            if current_slot.allowed_type == target_type:
                region_coords.append(current)
                neighbors = self.get_neighbors(current)
                for neighbor in neighbors:
                    if neighbor not in visited:
                        to_visit.append(neighbor)
        return region_coords


class PlayerBoard:
    """
    Contient :
    - la carte HexMap (toutes les cases)
    - les régions pré-calculées
    - les actions de placement
    - les checks de complétion de région
    """

    def __init__(self, layout_id: int):
        # construit la grille selon le duché choisi
        self.hex_map = HexMap(layout_id=layout_id)

        # régions pré-calculées à partir de la map
        self.regions: List[Region] = self._build_regions()

    def _build_regions(self) -> List[Region]:
        """
        Parcourt la carte, groupe les Slots connectés par allowed_type,
        crée les objets Region, et renvoie la liste.
        """
        regions: List[Region] = []
        visited: Set[Tuple[int, int]] = set()
        next_region_id = 0

        for coord, slot in self.hex_map.grid.items():
            if coord in visited:
                continue

            # flood-fill pour trouver la zone connectée du même allowed_type
            blob_coords = self.hex_map.fill_region(coord)

            # Marquer comme visités
            for bc in blob_coords:
                visited.add(bc)

            # Construire la Region correspondante
            slots_in_region = [self.hex_map.grid[c] for c in blob_coords]
            region = Region(
                region_id=next_region_id,
                allowed_type=slot.allowed_type,
                slots=slots_in_region,
            )
            regions.append(region)
            next_region_id += 1

        return regions

    def get_region_by_coord(self, coord: Tuple[int, int]) -> Optional[Region]:
        """
        Récupère l'objet Region (déjà pré-calculé) contenant cette coordonnée.
        """
        for region in self.regions:
            for slot in region.slots:
                if slot.coord == coord:
                    return region
        return None

    def can_place_tile_at(self, tile: Tile, coord: Tuple[int, int]) -> Optional[bool]:
        """
        Vérifie si la tuile peut être placée sur ce coord :
        - coord existe
        - slot pas occupé
        - type compatible
        (Ici on ne vérifie PAS les règles globales genre 'doit être adjacent à une tuile déjà posée')
        """
        if coord not in self.hex_map.grid:
            return False
        slot = self.hex_map.get_slot(coord)
        return slot.can_place_tile(tile)

    def place_tile(
        self, tile: Tile, coord: Tuple[int, int], current_round: int
    ) -> dict:
        """
        Place une tuile sur le board du joueur, puis met à jour les régions:
        - pose la tuile
        - vérifie si la région vient d'être complétée
        - renvoie un résumé utile (score potentiel, région complétée, etc.)
        """
        if not self.can_place_tile_at(tile, coord):
            raise ValueError(f"Illegal placement at {coord} for tile {tile}")

        slot = self.hex_map.get_slot(coord)
        if slot:
            slot.place_tile(tile)

        # Vérifier complétion de la région qui contient ce slot
        region = self.get_region_by_coord(coord)
        region_completed_now = False
        region_size = region.size() if region else 0

        if region and region.is_completed() and not region.has_scored:
            region_completed_now = True
            region.scored(current_round)

        # Renvoie des infos que le moteur de jeu (Game / VictoryPointTracker) peut utiliser
        return {
            "coord": coord,
            "placed_tile_type": tile.tile_type if tile else None,
            "region_id": region.region_id if region else None,
            "region_type": region.allowed_type if region else None,
            "region_size": region_size,
            "region_completed_now": region_completed_now,
            "completion_round": current_round if region_completed_now else None,
        }

    def get_all_completed_regions(self) -> List[Region]:
        """Utile en fin de partie pour scorer les bonus qui dépendent des regions complètes."""
        return [r for r in self.regions if r.is_completed()]

    def debug_print_board(self) -> None:
        """
        Méthode utilitaire facultative pour affichage texte.
        Montre coord -> (type, occupé)
        """
        for coord, slot in sorted(self.hex_map.grid.items()):
            print(coord, slot.allowed_type, "OCCUPIED" if slot.is_occupied else "free")


# temp for goods and tiles
class GoodsColor(Enum):
    """
    Type de marchandise (correspond aux 6 couleurs de tuiles marchandises).
    La couleur réelle n'a pas d'importance pour le moteur, juste l'identité.
    """

    COLOR_1 = 1
    COLOR_2 = 2
    COLOR_3 = 3
    COLOR_4 = 4
    COLOR_5 = 5
    COLOR_6 = 6


class GoodsTile:
    """
    Tuile marchandise (carrée dans le jeu physique).
    """

    def __init__(self, color: GoodsColor) -> None:
        self.color = color


class Board:
    """
    Plateau central des Châteaux de Bourgogne (version base, 4 joueurs).

    Il gère :
    - les 6 dépôts numérotés (1–6) contenant des tuiles hexagonales
    - le dépôt noir central
    - les marchandises sur les dépôts
    - les phases (A–E) et manches (1–5 / phase)
    - les piles de tuiles à piocher (hex et noires) et les piles de marchandises

    Remarque : ici on se concentre sur la logique de distribution / prise de tuiles.
    Tout ce qui concerne le score, l’argent, les ouvriers, etc. est plutôt du
    ressort d’une classe Game / Engine par dessus. :contentReference[oaicite:1]{index=1}
    """

    PHASES = ("A", "B", "C", "D", "E")

    def __init__(self, seed: Optional[int] = None) -> None:
        # Pour l’instant on implémente le plateau 4 joueurs (recto du plateau)
        self._rng = random.Random(seed)

        # Dépôts numérotés 1..6 -> liste de tuiles
        self.depots: Dict[int, List[Tile]] = {i: [] for i in range(1, 7)}
        # Marchandises posées sur chaque dépôt
        self.depot_goods: Dict[int, List[GoodsTile]] = {i: [] for i in range(1, 7)}
        # Dépôt noir (8 tuiles noires / phase)
        self.black_depot: List[Tile] = []

        # Pioches
        self._hex_supply: List[Tile] = self._build_colored_hex_supply()
        self._black_supply: List[Tile] = self._build_black_hex_supply()

        # Marchandises : 42 tuiles, 7 de chaque couleur, réparties en 5 piles de phase
        self._goods_stacks_by_phase: List[List[GoodsTile]] = self._build_goods_stacks()
        # Ce qui reste peut servir à distribuer 3 marchandises à chaque joueur au setup
        self.remaining_goods_for_players: List[GoodsTile] = []

        # Phase / manche
        self.current_phase_index: int = -1  # -1 => pas encore démarré
        self.round_in_phase: int = 0  # 0..5 (0 = pas encore joué de manche)
        # Pile de 5 marchandises pour la phase courante (une par manche)
        self._current_phase_round_goods: List[GoodsTile] = []

        # Démarre la phase A
        self.start_next_phase()

    # pioches

    def _build_colored_hex_supply(self) -> List[Tile]:
        """
        Construit la pioche des tuiles « normales » (non noires).

        D’après le matériel de jeu de la version de base : 40 bâtiments,
        20 animaux, 20 monastères, 14 châteaux, 10 mines, 20 bateaux,
        soit 124 tuiles. :contentReference[oaicite:2]{index=2}

        Complexité : O(N) pour N tuiles construites.
        """
        supply: List[Tile] = []
        supply.extend(Tile(TileType.BUILDING) for _ in range(40))
        supply.extend(Tile(TileType.ANIMAL) for _ in range(20))
        supply.extend(Tile(TileType.KNOWLEDGE) for _ in range(20))
        supply.extend(Tile(TileType.CASTLE) for _ in range(14))
        supply.extend(Tile(TileType.MINE) for _ in range(10))
        supply.extend(Tile(TileType.SHIP) for _ in range(20))
        self._rng.shuffle(supply)
        return supply

    def _build_black_hex_supply(self) -> List[Tile]:
        """
        Construit la pioche des tuiles noires (dépôt central).

        Comptage d’après les règles : 16 bâtiments noirs, 8 animaux noirs,
        6 monastères noirs, 2 châteaux noirs, 2 mines noires, 6 bateaux noirs,
        soit 40 tuiles (exactement 8 par phase). :contentReference[oaicite:3]{index=3}

        Complexité : O(N).
        """
        supply: List[Tile] = []
        supply.extend(Tile(TileType.BUILDING, is_black=True) for _ in range(16))
        supply.extend(Tile(TileType.ANIMAL, is_black=True) for _ in range(8))
        supply.extend(Tile(TileType.KNOWLEDGE, is_black=True) for _ in range(6))
        supply.extend(Tile(TileType.CASTLE, is_black=True) for _ in range(2))
        supply.extend(Tile(TileType.MINE, is_black=True) for _ in range(2))
        supply.extend(Tile(TileType.SHIP, is_black=True) for _ in range(6))
        self._rng.shuffle(supply)
        return supply

    def _build_goods_stacks(self) -> List[List[GoodsTile]]:
        """
        Construit les 5 piles de marchandises (A..E), 5 tuiles chacune.

        Les règles indiquent 42 marchandises, 7 de chaque couleur. On en
        utilise 25 pour les phases, le reste pour distribuer 3 tuiles à chaque
        joueur au setup. :contentReference[oaicite:4]{index=4}

        Complexité : O(G) pour G marchandises.
        """
        goods: List[GoodsTile] = []
        for color in GoodsColor:
            goods.extend(GoodsTile(color) for _ in range(7))
        self._rng.shuffle(goods)

        stacks: List[List[GoodsTile]] = []
        for i in range(5):
            stacks.append(goods[i * 5 : (i + 1) * 5])
        self.remaining_goods_for_players = goods[25:]
        return stacks

    # phases

    @property
    def current_phase(self) -> str:
        """Renvoie la lettre de phase actuelle ('A'..'E'). O(1)."""
        if self.current_phase_index < 0:
            return "?"
        return self.PHASES[self.current_phase_index]

    def start_next_phase(self) -> None:
        """
        Passe à la phase suivante (A → B → ... → E) et met en place :
        - vidage des dépôts (mais pas les marchandises déjà posées)
        - remplissage des 6 dépôts numérotés (4 tuiles chacun)
        - remplissage du dépôt noir (8 tuiles)
        - préparation des 5 marchandises de manche pour la phase

        Complexité : O(D + T) où D = nombre de dépôts (constante 7),
        T = tuiles à distribuer (constante par phase).
        """
        if self.current_phase_index + 1 >= len(self.PHASES):
            raise RuntimeError("Tous les tours sont déjà terminés.")

        self.current_phase_index += 1
        self.round_in_phase = 0

        # Vider les dépôts de tuiles (les marchandises restent)
        for depot_id in range(1, 7):
            self.depots[depot_id].clear()
        self.black_depot.clear()

        # Re-remplir les dépôts numérotés : 4 tuiles chacun en 4 joueurs
        for depot_id in range(1, 7):
            for _ in range(4):
                if not self._hex_supply:
                    raise RuntimeError("Plus de tuiles hex à distribuer.")
                self.depots[depot_id].append(self._hex_supply.pop())

        # Re-remplir le dépôt noir : 8 tuiles
        for _ in range(8):
            if not self._black_supply:
                raise RuntimeError("Plus de tuiles noires à distribuer.")
            self.black_depot.append(self._black_supply.pop())

        # Préparer les marchandises de la phase courante
        self._current_phase_round_goods = list(
            self._goods_stacks_by_phase[self.current_phase_index]
        )

    def is_phase_over(self) -> bool:
        """Retourne True si les 5 manches de la phase sont jouées. O(1)."""
        return self.round_in_phase >= 5

    def advance_round(self, white_die_result: int) -> Optional[GoodsTile]:
        """
        Avance d'une manche :
        - prend la prochaine marchandise de la piste de manche
        - la place sur le dépôt correspondant au résultat du dé blanc

        Renvoie la marchandise posée (ou None si plus de marchandise).

        Complexité : O(1).
        """
        if not (1 <= white_die_result <= 6):
            raise ValueError("white_die_result doit être entre 1 et 6.")

        if self.is_phase_over():
            # Pas d'erreur sévère : simplement aucune marchandise à poser
            return None

        goods_tile = self._current_phase_round_goods[self.round_in_phase]
        self.depot_goods[white_die_result].append(goods_tile)
        self.round_in_phase += 1
        return goods_tile

    # actions du jeu

    def take_hex_from_depot(self, depot_id: int) -> Tile:
        """
        Retire et renvoie une tuile hex du dépôt numéroté donné.

        Utilisée pour l'action « prendre une tuile du plateau ». :contentReference[oaicite:5]{index=5}

        Complexité : O(1) sur la taille de la liste de ce dépôt.
        """
        if depot_id not in self.depots:
            raise ValueError(f"Depot {depot_id} does not exist.")
        if not self.depots[depot_id]:
            raise ValueError(f"Depot {depot_id} is empty.")
        return self.depots[depot_id].pop()

    def take_hex_from_black_depot(self) -> Tile:
        """
        Retire et renvoie une tuile du dépôt noir central (achat pour 2 argent).

        Complexité : O(1).
        """
        if not self.black_depot:
            raise ValueError("Black depot is empty.")
        return self.black_depot.pop()

    def take_all_goods_from_depot(self, depot_id: int) -> List[GoodsTile]:
        """
        Utilisée quand un joueur place un bateau : il prend toutes les
        marchandises d'un dépôt de son choix. :contentReference[oaicite:6]{index=6}

        Renvoie la liste des marchandises et vide ce dépôt.

        Complexité : O(k) où k est le nombre de marchandises sur ce dépôt.
        """
        if depot_id not in self.depot_goods:
            raise ValueError(f"Depot {depot_id} does not exist.")
        goods = self.depot_goods[depot_id]
        self.depot_goods[depot_id] = []
        return goods

    def debug_print_state(self) -> None:
        """
        Affichage texte simple de l’état du plateau central
        (pour debug / tests manuels). O(D + G).

        D = nombre de dépôts, G = nombre de marchandises.
        """
        print(f"Phase {self.current_phase} / round {self.round_in_phase + 1}")
        print("Depots:")
        for depot_id in range(1, 7):
            tiles = self.depots[depot_id]
            goods = self.depot_goods[depot_id]
            tile_types = [t.tile_type.name for t in tiles]
            goods_colors = [g.color.name for g in goods]
            print(f"  {depot_id}: hex={tile_types}  goods={goods_colors}")
        print("Black depot:", [t.tile_type.name for t in self.black_depot])


PlayerBoard(layout_id=1)
Piece_Animal = Animal(AnimalType.CATTLE, 3, Color.RED)
Tile_animal = Tile(TileType.ANIMAL, False)
Tile_animal.tile = Piece_Animal
board = PlayerBoard(layout_id=1)
board.place_tile(Tile_animal, (0, -3), 1)
print("runned")
