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
        """A appeler qd la region score pour pas qu'elle re rapporte des points"""
        self.has_scored = True


LAYOUTS = {
    1: {
        # Exemple de layout
        (0, 0): TileType.CASTLE,
        (1, 0): TileType.SHIP,
        (2, 0): TileType.SHIP,
        (3, 0): TileType.SHIP,
        (-1, 0): TileType.SHIP,
        (-2, 0): TileType.SHIP,
        (-3, 0): TileType.SHIP,
        (0, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
        (0, -1): TileType.BUILDING,
    }
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
    def __init__(self, map: HexMap):
        self.map = map
