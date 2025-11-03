from enum import Enum
from typing import Optional, Dict, List, Tuple, Set


class TileType(Enum):
    CASTLE = "castle"
    BUILDING = "building"
    SHIP = "ship"
    MINE = "mine"
    ANIMAL = "animal"
    KNOWLEDGE = "knowledge"


class Tile:
    tile_type: TileType


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
        (0, -3): TileType.CASTLE,
        (1, -3): TileType.CASTLE,
        (2, -3): TileType.KNOWLEDGE,
        (3, -3): TileType.BUILDING,
        # r = -2 (q = -1..3)
        (-1, -2): TileType.CASTLE,
        (0, -2): TileType.ANIMAL,
        (1, -2): TileType.KNOWLEDGE,
        (2, -2): TileType.BUILDING,
        (3, -2): TileType.BUILDING,
        # r = -1 (q = -2..3)
        (-2, -1): TileType.ANIMAL,
        (-1, -1): TileType.ANIMAL,
        (0, -1): TileType.BUILDING,
        (1, -1): TileType.KNOWLEDGE,
        (2, -1): TileType.MINE,
        (3, -1): TileType.SHIP,
        # r = 0 (q = -3..3)
        (-3, 0): TileType.ANIMAL,
        (-2, 0): TileType.BUILDING,
        (-1, 0): TileType.SHIP,
        (0, 0): TileType.SHIP,
        (1, 0): TileType.SHIP,
        (2, 0): TileType.BUILDING,
        (3, 0): TileType.MINE,
        # r = 1 (q = -3..2)
        (-3, 1): TileType.ANIMAL,
        (-2, 1): TileType.SHIP,
        (-1, 1): TileType.MINE,
        (0, 1): TileType.BUILDING,
        (1, 1): TileType.BUILDING,
        (2, 1): TileType.MINE,
        # r = 2 (q = -3..1)
        (-3, 2): TileType.SHIP,
        (-2, 2): TileType.MINE,
        (-1, 2): TileType.MINE,
        (0, 2): TileType.KNOWLEDGE,
        (1, 2): TileType.KNOWLEDGE,
        # r = 3 (q = -3..0)
        (-3, 3): TileType.BUILDING,
        (-2, 3): TileType.MINE,
        (-1, 3): TileType.MINE,
        (0, 3): TileType.KNOWLEDGE,
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

    def can_place_tile_at(self, tile: Tile, coord: Tuple[int, int]) -> bool:
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
        return slot.can_place(tile)

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
        slot.place_tile(tile)

        # Vérifier complétion de la région qui contient ce slot
        region = self.get_region_by_coord(coord)
        region_completed_now = False
        region_size = region.size() if region else 0

        if region and region.is_complete() and not region.has_scored:
            region_completed_now = True
            region.mark_completed(current_round)

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
        return [r for r in self.regions if r.is_complete()]

    def debug_print_board(self) -> None:
        """
        Méthode utilitaire facultative pour affichage texte.
        Montre coord -> (type, occupé)
        """
        for coord, slot in sorted(self.hex_map.grid.items()):
            print(coord, slot.allowed_type, "OCCUPIED" if slot.is_occupied else "free")
