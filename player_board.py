from typing import List, Optional, Set, Tuple
from board import *
from player_board import *
from buildings import *

class PlayerBoard:
    """
    Contient :
    - la carte HexMap (toutes les cases)
    - les régions pré-calculées
    - les actions de placement
    - les checks de complétion de région
    """

    def __init__(self, layout_id: int, player: Player):
        # construit la grille selon le duché choisi
        self.hex_map = HexMap(layout_id=layout_id)

        # régions pré-calculées à partir de la map
        self.regions: List[Region] = self._build_regions()

        self.player = player

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
        # check if there are neighors nearby that are occupied
        neighbors = self.hex_map.get_neighbors(coord)
        neighors_occupied = False
        for neigh in neighbors:
            neighor_slot = self.hex_map.get_slot(neigh)
            if neighor_slot.is_occupied:
                neighors_occupied = True
                break
        region = self.get_region_by_coord(coord)
        if region.allowed_type == TileType.ANIMAL or tile.tile_type in self.player.yellow_effects:
            allowed = True
        else:
            allowed = False
        return slot.can_place_tile(tile) and (neighors_occupied) and allowed

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