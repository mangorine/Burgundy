from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from game import Game


class ActionType(Enum):
    """
    On créer une classe Enum ActionType pour avoir toutes les actions globales possibles.
    """
    # Main actions (require a die)
    TAKE_TILE = "take a tile from depot"
    PLACE_TILE = "place a tile from storage"
    SELL_GOODS = "sell goods of a color"
    TAKE_WORKERS = "take worker chips"
    
    # Additional actions (don't require a die)
    BUY_BLACK_TILE = "buy a tile from black depot"
    ADJUST_DIE = "adjust die value with workers"
    
    # Free actions (can be done anytime)
    DISCARD_TILE = "discard a tile from storage"


@dataclass(frozen=True)
class Action:
    """
    Comme certaines actions ont des sous actions, on créer une classe à part entière qui prend en compte l'Enum au dessus.
    
    Attributes:
        type: The type of action (from ActionType enum)
        params: Parameters specific to this action
        cost: Resources required (workers, silverlings, dice)
        description: Human-readable description of the action
    """
    type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    cost: Dict[str, int] = field(default_factory=dict)
    description: str = ""


class MoveGenerator:
    """
    Cette classe est pour générer tous les coups possibles pour un joueur durant son tour.
    Elle prend en compte l'état actuel du jeu et les ressources du joueur pour déterminer 
    toutes les actions valides qu'il peut effectuer.
    
    Usage:
        generator = MoveGenerator(game, player)
        all_moves = generator.get_all_possible_moves()
    """
    
    def __init__(self, game: "Game", player: "Player") -> None:
        """
        Initialise le générateur de coups avec l'état actuel du jeu.
        
        Args:
            game: L'instance actuelle du jeu
            player: Le joueur pour lequel on veut générer les coups
        """
        self.game = game
        self.player = player
        self.board = game.board
    
    def get_all_possible_moves(self) -> List[Action]:
        """
        Ici, on rassemble tous les coups possibles mais les fonctions qu'on utilise sont en-dessous.
        C'est un peu un wrapper ce truc.

        Returns:
            List of all valid Action objects the player can perform.
        """
        moves: List[Action] = []
        
        # Main actions (require dice)
        moves.extend(self.get_take_tile_moves())
        moves.extend(self.get_place_tile_moves())
        moves.extend(self.get_sell_goods_moves())
        moves.extend(self.get_take_workers_moves())
        
        # Additional actions
        moves.extend(self.get_buy_black_tile_moves())
        
        # Free actions
        moves.extend(self.get_discard_tile_moves())
        
        return moves
    
    def get_take_tile_moves(self) -> List[Action]:
        """
        Tout ce qui a trait aux tuiles du milieu en gros, si on peut prendre une tuile, c'est un move à ajouter.
        
        Returns:
            List of valid take tile actions
        """
        moves: List[Action] = []
        
        if not self.player.can_store_hex_tile():
            return moves  # No storage space
        
        if len(self.player.dice) == 0:
            return moves  # No dice available
        
        for depot_id in range(1, 7):
            # Check if depot has tiles
            if not self.board.depots[depot_id]:
                continue
            
            can_take, die_value, workers_needed = self.player.can_use_die_for_depot(depot_id)
            
            if can_take:
                # Check if player has yellow tile 12 for free adjustment
                has_free_adjustment = self.player.can_take_from_depot_with_adjustment()
                if has_free_adjustment and workers_needed > 0:
                    workers_needed = max(0, workers_needed - 1)
                
                # List available tiles in depot (for informational purposes)
                available_tiles = [t.tile_type.name for t in self.board.depots[depot_id]]
                
                move = Action(
                    type=ActionType.TAKE_TILE,
                    params={
                        "depot_id": depot_id,
                        "die_value": die_value,
                        "available_tiles": available_tiles
                    },
                    cost={"die": die_value, "workers": workers_needed},
                    description=f"Take tile from depot {depot_id} (die {die_value}, {workers_needed} workers)"
                )
                moves.append(move)
        
        return moves
    
    def get_place_tile_moves(self) -> List[Action]:
        """
        Les joueurs ont des tuiles dans leur "inventaire" et peuvent utiliser un dé pour en placer une sur leur plateau.
        Chaque tuile que le joueur peut placer est un coup possible.
        
        A player can place a tile from their storage onto their board if:
        - They have tiles in storage
        - They have a die matching the slot's dice value (or can adjust)
        - The tile type matches the slot's allowed type
        - The slot is adjacent to an already-placed tile
        
        Returns:
            List of valid place tile actions
        """
        moves: List[Action] = []
        
        if len(self.player.hex_storage) == 0:
            return moves  # No tiles in storage
        
        if len(self.player.dice) == 0:
            return moves  # No dice available
        
        for storage_idx, tile in enumerate(self.player.hex_storage):
            # Find all valid coordinates for this tile
            for coord, slot in self.player.board.hex_map.grid.items():
                # Check if this tile can be placed here
                if not self.player.board.can_place_tile_at(tile, coord, self.player):
                    continue
                
                can_place, die_value, workers_needed = self.player.can_use_die_for_placement(coord)
                
                if can_place:
                    move = Action(
                        type=ActionType.PLACE_TILE,
                        params={
                            "storage_index": storage_idx,
                            "coord": coord,
                            "tile_type": tile.tile_type.name,
                            "die_value": die_value
                        },
                        cost={"die": die_value, "workers": workers_needed},
                        description=f"Place {tile.tile_type.name} at {coord} (die {die_value}, {workers_needed} workers)"
                    )
                    moves.append(move)
        
        return moves
    
    def get_sell_goods_moves(self) -> List[Action]:
        """
        Pour rappel, pour vendre un good, il faut que le joueur ait le dé qui correspond à la couleur du truc.
        Donc si le joueur a des goods dans son inventaire et le bon dé, il peut vendre.
        Le dé peut être ajusté avec des workers aussi.
        
        Returns:
            List of valid sell goods actions
        """
        moves: List[Action] = []
        
        if len(self.player.goods_storage) == 0:
            return moves  # No goods to sell
        
        if len(self.player.dice) == 0:
            return moves  # No dice available
        
        # Get unique colors in goods storage
        from board import GoodsColor
        available_colors = set()
        for goods in self.player.goods_storage:
            available_colors.add(goods.color)
        
        for color in available_colors:
            # The required die value matches the color's value (COLOR_1 = 1, COLOR_2 = 2, etc.)
            required_die_value = color.value
            
            # Count goods of this color
            count = sum(1 for g in self.player.goods_storage if g.color == color)
            
            # Check if player has exact die or can adjust with workers
            can_sell = False
            die_to_use = 0
            workers_needed = 0
            
            # First check for exact match
            if required_die_value in self.player.dice:
                can_sell = True
                die_to_use = required_die_value
                workers_needed = 0
            else:
                # Check if we can reach required value using workers
                best_option: Tuple[bool, int, int] = (False, 0, 999)
                for die_value in self.player.dice:
                    can_reach, workers_cost = self.player.can_reach_value_with_workers(
                        required_die_value, die_value
                    )
                    if can_reach and workers_cost < best_option[2]:
                        best_option = (True, die_value, workers_cost)
                
                if best_option[0]:
                    can_sell = True
                    die_to_use = best_option[1]
                    workers_needed = best_option[2]
            
            if can_sell:
                silverlings = self.player.get_silverlings_per_good_sold() * count
                
                move = Action(
                    type=ActionType.SELL_GOODS,
                    params={
                        "color": color.name,
                        "count": count,
                        "die_value": die_to_use,
                        "required_die_value": required_die_value
                    },
                    cost={"die": die_to_use, "workers": workers_needed},
                    description=f"Sell {count} {color.name} goods for {silverlings} silverlings (die {die_to_use}, {workers_needed} workers)"
                )
                moves.append(move)
        
        return moves
    
    def get_take_workers_moves(self) -> List[Action]:
        moves: List[Action] = []
        if len(self.player.dice) == 0:
            return moves
        
        workers_gained = self.player.get_workers_from_take_action()
        silverling_bonus = self.player.get_silverling_bonus_on_take_workers()
        
        # On utilise un set pour ne pas proposer 2 fois la même action si on a deux dés '4'
        processed_die_values = set()

        for die_value in self.player.dice:
            if die_value in processed_die_values:
                continue
                
            processed_die_values.add(die_value)
            bonus_text = f" + {silverling_bonus} silverling" if silverling_bonus > 0 else ""
            
            move = Action(
                type=ActionType.TAKE_WORKERS,
                params={
                    "die_value": die_value, # Le joueur peut choisir quel dé sacrifier
                    "workers_gained": workers_gained,
                    "silverling_bonus": silverling_bonus
                },
                cost={"die": die_value},
                description=f"Take {workers_gained} workers{bonus_text} (die {die_value})"
            )
            moves.append(move)
        
        return moves
    
    def get_buy_black_tile_moves(self) -> List[Action]:
        """
        On crée les moves pour acheter une tuile noire.
        
        Returns:
            List of valid buy black tile actions
        """
        moves: List[Action] = []
        
        if not self.player.can_store_hex_tile():
            return moves  # No storage space
        
        if self.player.silverlings < 2:
            return moves  # Not enough silverlings
        
        if not self.board.black_depot:
            return moves  # Black depot is empty
        
        # List available tiles in black depot
        available_tiles = [t.tile_type.name for t in self.board.black_depot]
        
        move = Action(
            type=ActionType.BUY_BLACK_TILE,
            params={
                "available_tiles": available_tiles
            },
            cost={"silverlings": 2},
            description=f"Buy tile from black depot for 2 silverlings"
        )
        moves.append(move)
        
        return moves
    
    def get_discard_tile_moves(self) -> List[Action]:
        """
        A tout moment, le joueur peut défausser une tuile de son inventaire.
        
        
        Returns:
            List of valid discard tile actions
        """
        moves: List[Action] = []
        
        for idx, tile in enumerate(self.player.hex_storage):
            move = Action(
                type=ActionType.DISCARD_TILE,
                params={
                    "storage_index": idx,
                    "tile_type": tile.tile_type.name
                },
                cost={},
                description=f"Discard {tile.tile_type.name} from storage (slot {idx})"
            )
            moves.append(move)
        
        return moves
    
    def get_moves_by_type(self, action_type: ActionType) -> List[Action]:
        """
        Fonction helper pour obtenir tous les moves d'un type spécifique.
        
        Args:
            action_type: The type of action to filter by
            
        Returns:
            List of valid actions of the specified type
        """
        all_moves = self.get_all_possible_moves()
        return [m for m in all_moves if m.type == action_type]
    
    def get_moves_for_die(self, die_value: int) -> List[Action]:
        """
        Obtenir tous les moves possibles qui peuvent utiliser une valeur de dé spécifique.
        
        Args:
            die_value: The die value to filter by
            
        Returns:
            List of valid actions that can use this die
        """
        all_moves = self.get_all_possible_moves()
        result = []
        for move in all_moves:
            if move.cost.get("die") == die_value or "die" not in move.cost:
                result.append(move)
        return result
    
    def has_any_moves(self) -> bool:
        """
        Hyper utile pour savoir si le joueur peut faire quelque chose ou pas.
        
        Returns:
            True if at least one valid move exists
        """
        return len(self.get_all_possible_moves()) > 0
    
    def count_moves(self) -> Dict[str, int]:
        """
        Fonction helper pour compter le nombre de moves par type.
        
        Returns:
            Dictionary mapping action type names to their count
        """
        all_moves = self.get_all_possible_moves()
        counts: Dict[str, int] = {}
        for move in all_moves:
            type_name = move.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def __repr__(self) -> str:
        counts = self.count_moves()
        total = sum(counts.values())
        return f"MoveGenerator({self.player.name}: {total} moves available - {counts})"