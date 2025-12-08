from typing import List, Optional, Dict, Any

# On suppose que tout ça est dans le même module que ton code original.
# Sinon, adapte les imports : from boards import Board, Tile, TileType, GoodsTile, PlayerBoard
# Ici, TileType, Board, GoodsTile, PlayerBoard, Player, etc. sont déjà définis.

from animals import Animal, AnimalType
from buildings import Building, BuildingType

# Si tu as une classe Knowledge / KnowledgeType pour les tuiles jaunes :
try:
    from buildings import Knowledge, KnowledgeType  # ou autre module
except ImportError:
    Knowledge = object  # fallback pour éviter les crash si non dispo
    KnowledgeType = object


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
        layouts: List[int],
        seed: Optional[int] = None,
    ) -> None:
        """
        Crée une partie avec N joueurs.

        - player_names : liste des noms ("Alice", "Bob", ...)
        - layouts : liste des layout_id pour chaque joueur (ex : [1,2,3,1])
        - seed : graine pour le random du Board

        Complexité : O(P * N) où P = nb joueurs, N = taille d'un PlayerBoard.
        """
        if len(player_names) != len(layouts):
            raise ValueError("Il faut autant de noms que de layout_id.")

        self.board = Board(seed=seed)
        self.players: List[Player] = [
            Player(name=player_names[i], layout_id=layouts[i])
            for i in range(len(player_names))
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
        Complexité : O(1).
        """
        return self.players[self.current_player_index]

    def next_player(self) -> None:
        """
        Passe au joueur suivant (ordre simple pour l'instant).
        Complexité : O(1).
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    # =============================
    # Actions principales du jeu
    # =============================

    def action_take_hex_from_depot(self, depot_id: int) -> None:
        """
        Action : le joueur courant prend une tuile hex du dépôt donné
        et la met dans sa réserve perso.

        Complexité : O(1) (Board.take_hex_from_depot + Player.add_hex_to_storage).
        """
        player = self.current_player
        if not player.can_store_hex_tile():
            raise ValueError(f"{player.name} ne peut pas stocker plus de tuiles.")

        tile = self.board.take_hex_from_depot(depot_id)
        player.add_hex_to_storage(tile)

    def action_take_hex_from_black_depot(self) -> None:
        """
        Action : le joueur courant achète une tuile noire pour 2 écus.

        Complexité : O(1).
        """
        player = self.current_player
        player.spend_silverlings(2)
        tile = self.board.take_hex_from_black_depot()
        player.add_hex_to_storage(tile)

    def action_take_goods_from_ship(self, depot_id: int) -> None:
        """
        Action complémentaire : prendre toutes les marchandises d'un dépôt
        (par exemple après avoir posé un bateau).

        Complexité : O(k) où k = nb de marchandises dans le dépôt.
        """
        player = self.current_player
        goods = self.board.take_all_goods_from_depot(depot_id)
        player.add_goods(goods)

    def action_place_tile_from_storage(
        self,
        storage_index: int,
        coord: tuple[int, int],
        current_round: int,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Action : le joueur courant pose une tuile de sa réserve sur son plateau.

        - storage_index : indice dans player.hex_storage
        - coord : coordonnée hex sur le PlayerBoard
        - current_round : numéro de manche/round global
        - extra_context : infos supplémentaires pour certains effets
            (ex : choix du dépôt pour un bateau, couleur à vendre, etc.)

        Complexité :
        - O(1) pour retirer de la réserve
        - O(1) pour la pose (ton PlayerBoard)
        - O(k) pour l'effet de la tuile (k dépend du type, ex taille de région)
        -> O(k) global.
        """
        if extra_context is None:
            extra_context = {}

        player = self.current_player

        # 1) On récupère la tuile à poser
        tile = player.remove_hex_from_storage(storage_index)

        # 2) On la pose sur le PlayerBoard
        placement_result = player.board.place_tile(tile, coord, current_round)

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

        Complexité : O(1) + coût de la fonction appelée.
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
        Applique l'effet d'un bâtiment (green tile).

        building_obj est une instance de ta classe Building
        (avec un BuildingType accessible).

        Complexité : O(1) en général (les effets sont locaux).
        """
        btype = getattr(building_obj, "building_type", None)

        # Exemple concret : WAREHOUSE (ton test l'utilise déjà)
        # -> Le joueur choisit un dépôt de marchandises et prend tout.
        if btype == BuildingType.WAREHOUSE:
            depot_id = ctx.get("goods_depot_choice")
            if depot_id is None:
                # Pas de choix fourni : on ne fait rien (ou lever une erreur selon ta logique).
                return
            goods = self.board.take_all_goods_from_depot(depot_id)
            player.add_goods(goods)
            # Petit bonus générique de PV (optionnel) :
            player.gain_victory_points(len(goods))

        else:
            # Effet standard générique pour les autres bâtiments :
            # par exemple +2 PV à chaque bâtiment posé.
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

        Complexité : O(1).
        """
        return

    def end_phase(self) -> None:
        """
        À appeler quand une phase (A..E) se termine.

        - Distribue l'argent des mines
        - Passe à la phase suivante sur Board

        Complexité : O(P * N) où P = nb joueurs, N = nb de cases du PlayerBoard
        (on parcourt les slots pour compter les mines).
        """
        # 1) Mines → argent
        for player in self.players:
            nb_mines = 0
            for region in player.board.regions:
                for slot in region.slots:
                    if slot.is_occupied and slot.tile.tile_type == TileType.MINE:
                        nb_mines += 1
            # Règle simple : 1 mine = 1 écu par manche de phase
            player.gain_silverlings(nb_mines)

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

        Complexité : O(1) + O(k) pour k marchandises sur le dépôt.
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

        Complexité : O(1).
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

        Complexité : O(S) où S = taille de la région.
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
        C'est à l'UI / IA de l'exploiter.

        Complexité : O(1).
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

        Complexité : O(1).
        """
        size = placement_result.get("region_size", 0)
        player.gain_victory_points(size)
