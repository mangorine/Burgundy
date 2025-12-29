from typing import List, Optional, Dict, Any
from board import Board, Tile, TileType, GoodsTile
from player import Player
from animals import Animal, AnimalType
from buildings import Building, BuildingType

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
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Action : le joueur courant pose une tuile de sa réserve sur son plateau.

        - storage_index : indice dans player.hex_storage
        - coord : coordonnée hex sur le PlayerBoard
        - current_round : numéro de manche/round global
        - extra_context : infos supplémentaires pour certains effets
            (ex : choix du dépôt pour un bateau, couleur à vendre, etc.)
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
            nested_ctx = extra.get("extra_context", {})

            # IMPORTANT : on NE touche PAS à self.current_player
            # on réutilise simplement la logique standard de pose
            self.action_place_tile_from_storage(
                storage_index,
                extra_coord,
                current_round,
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
