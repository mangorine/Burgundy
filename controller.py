"""
GameController - Controller Layer for Castles of Burgundy

This module implements the Controller in a clean architecture pattern:
- UI Layer: Handles user input and display (not implemented here)
- Controller Layer: Coordinates between UI and game logic (this module)
- Game Layer: Core game rules and state (game.py, player.py, board.py)

The controller is completely UI-agnostic and only deals with Action objects
and game state queries.
"""

from typing import List, Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from action import Action, ActionType, MoveGenerator
from game import Game, TurnManager
from player import Player
from board import Board, TileType, GoodsColor


class GamePhase(Enum):
    """Represents the current phase of a player's turn."""
    WAITING_FOR_TURN = auto()
    ROLLING_DICE = auto()
    SELECTING_ACTION = auto()
    EXECUTING_ACTION = auto()
    TURN_COMPLETE = auto()
    GAME_OVER = auto()


class ActionResult(Enum):
    """Result of attempting to execute an action."""
    SUCCESS = auto()
    INVALID_ACTION = auto()
    ILLEGAL_MOVE = auto()
    INSUFFICIENT_RESOURCES = auto()
    NOT_YOUR_TURN = auto()
    NO_ACTIONS_REMAINING = auto()


@dataclass
class ActionResponse:
    """
    Response object returned after attempting to execute an action.
    
    Attributes:
        result: The result status of the action attempt
        message: Human-readable description of what happened
        action: The action that was attempted
        game_state_changed: Whether the game state was modified
        extra_data: Additional data specific to the action (e.g., tiles taken, points gained)
    """
    result: ActionResult
    message: str
    action: Optional[Action] = None
    game_state_changed: bool = False
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GameStateView:
    """
    Immutable view of the current game state for the UI.
    
    This provides a read-only snapshot that the UI can safely use
    without risk of modifying game state.
    """
    current_player_name: str
    current_player_index: int
    current_phase: str
    round_in_phase: int
    global_round: int
    
    # Current player resources
    dice: Tuple[int, ...]
    silverlings: int
    workers: int
    victory_points: int
    hex_storage_count: int
    goods_count: int
    
    # Game progress
    actions_remaining: int
    is_game_over: bool
    
    # All players summary
    player_summaries: Tuple[Dict[str, Any], ...]


class RulesEngine:
    """
    Encapsulates game rules and legal move computation.
    
    This is a thin wrapper around MoveGenerator that provides
    a cleaner interface for the controller.
    """
    
    def __init__(self, game: Game) -> None:
        self.game = game
    
    def get_legal_actions(self, player: Player) -> List[Action]:
        """
        Compute all legal actions for a given player.
        
        Args:
            player: The player to compute actions for
            
        Returns:
            List of all legal Action objects
        """
        generator = MoveGenerator(self.game, player)
        return generator.get_all_possible_moves()
    
    def get_legal_actions_by_type(self, player: Player, action_type: ActionType) -> List[Action]:
        """
        Get legal actions filtered by type.
        
        Args:
            player: The player to compute actions for
            action_type: The type of action to filter by
            
        Returns:
            List of legal actions of the specified type
        """
        generator = MoveGenerator(self.game, player)
        return generator.get_moves_by_type(action_type)
    
    def is_action_legal(self, player: Player, action: Action) -> bool:
        """
        Check if a specific action is legal for a player.
        
        Args:
            player: The player attempting the action
            action: The action to validate
            
        Returns:
            True if the action is legal, False otherwise
        """
        legal_actions = self.get_legal_actions(player)
        
        # Compare action type and key parameters
        for legal in legal_actions:
            if self._actions_match(action, legal):
                return True
        return False
    
    def _actions_match(self, action1: Action, action2: Action) -> bool:
        """
        Check if two actions are equivalent.
        
        Actions match if they have the same type and key parameters.
        """
        if action1.type != action2.type:
            return False
        
        # Compare key parameters based on action type
        if action1.type == ActionType.TAKE_TILE:
            return action1.params.get("depot_id") == action2.params.get("depot_id")
        
        elif action1.type == ActionType.PLACE_TILE:
            return (action1.params.get("storage_index") == action2.params.get("storage_index") and
                    action1.params.get("coord") == action2.params.get("coord"))
        
        elif action1.type == ActionType.SELL_GOODS:
            return action1.params.get("color") == action2.params.get("color")
        
        elif action1.type == ActionType.TAKE_WORKERS:
            return True  # Any take workers action is equivalent
        
        elif action1.type == ActionType.BUY_BLACK_TILE:
            return True  # Any buy black tile action is equivalent
        
        elif action1.type == ActionType.DISCARD_TILE:
            return action1.params.get("storage_index") == action2.params.get("storage_index")
        
        return False


class GameController:
    """
    Controller layer that mediates between UI and game logic.
    
    Responsibilities:
    - Expose available actions to the UI
    - Validate submitted actions
    - Execute legal actions through the game logic
    - Manage turn progression
    - Provide read-only game state views
    
    The controller is completely UI-agnostic:
    - No UI imports
    - No click handling
    - No rendering logic
    
    Usage:
        controller = GameController(game)
        
        # UI queries available actions
        actions = controller.get_available_actions()
        
        # UI displays actions and user selects one
        chosen_action = actions[0]  # User's choice
        
        # UI submits action to controller
        response = controller.submit_action(chosen_action)
        
        # UI handles response
        if response.result == ActionResult.SUCCESS:
            # Update display
            pass
    """
    
    def __init__(self, game: Game, seed: Optional[int] = None) -> None:
        self._game = game
        self._turn_manager = TurnManager(game)  # Fixed: pass game, not seed
        self._rules_engine = RulesEngine(game)  # Added: missing initialization
        self._state_change_callbacks: List[Callable[[GameStateView], None]] = []  # Added: missing initialization
        self._turn_started = False
        self._round_started = False
        self._players_played_this_round = 0

    def start_round(self) -> ActionResponse:
        """
        Starts a new round: rolls the white die and places goods.
        """
        if self._game.is_game_over():
            return ActionResponse(
                result=ActionResult.GAME_OVER,
                message="The game is over."
            )

        # Check if the phase is over and start a new phase if needed
        if self._game.board.is_phase_over():
            phase_info = self._game.start_new_phase()
            if self._game.is_game_over():
                return ActionResponse(
                    result=ActionResult.GAME_OVER,
                    message=f"Game over after phase {phase_info['current_phase'] - 1}!"
                )

        round_info = self._game.start_new_round()
        self._round_started = True
        self._players_played_this_round = 0

        return ActionResponse(
            result=ActionResult.SUCCESS,
            message=f"Round {round_info['current_round']}/5 - Phase {round_info['current_phase']}. "
                    f"White die: {round_info['white_die']}. "
                    f"Goods placed: {round_info['goods_placed']}",
            extra_data=round_info
        )

    def start_turn(self) -> ActionResponse:
        """
        Starts the current player's turn.
        """
        if not self._round_started:
            return ActionResponse(
                result=ActionResult.INVALID_ACTION,
                message="The round has not started yet. Call start_round() first."
            )

        if self._turn_started:
            return ActionResponse(
                result=ActionResult.INVALID_ACTION,
                message="The turn has already started."
            )

        self._turn_manager.start_turn()
        self._turn_started = True

        player = self._game.current_player
        return ActionResponse(
            result=ActionResult.SUCCESS,
            message=f"{player.name}'s turn started.",
            extra_data={"player": player.name, "dice": player.dice}
        )

    def end_turn(self) -> ActionResponse:
        """Termine le tour du joueur courant et passe au suivant."""
        if not self._turn_started:
            return ActionResponse(
                result=ActionResult.INVALID_ACTION,
                message="Aucun tour en cours."
            )
        
        self._turn_manager.end_turn()
        self._turn_started = False
        self._players_played_this_round += 1
        
        # Vérifier si tous les joueurs ont joué cette manche
        if self._players_played_this_round >= len(self._game.players):
            self._round_started = False
            self._game.end_current_round()
            
            return ActionResponse(
                result=ActionResult.SUCCESS,
                message="Manche terminée. Appelez start_round() pour la prochaine manche.",
                extra_data={"round_over": True}  # Fixed: was 'data='
            )
        
        # Passer au joueur suivant
        self._game.next_player()
        
        return ActionResponse(
            result=ActionResult.SUCCESS,
            message=f"Tour terminé. Au tour de {self._game.current_player.name}.",
            extra_data={"round_over": False, "next_player": self._game.current_player.name}  # Fixed: was 'data='
        )

    def get_game_state(self) -> dict:
        """Retourne l'état complet du jeu."""
        return {
            "current_phase": self._game.board.current_phase,
            "current_round": self._game.board.round_in_phase,
            "current_player": self._game.current_player.name,
            "round_started": self._round_started,
            "turn_started": self._turn_started,
            "is_game_over": self._game.is_game_over(),
            "goods_depots": {
                i: len(depot) for i, depot in enumerate(self._game.board.goods_depots)
            },
        }
    
    def force_end_turn(self) -> ActionResponse:
        """
        Force end the current turn (e.g., if player passes remaining actions).
        
        Returns:
            ActionResponse indicating success or failure
        """
        if not self._turn_started:
            return ActionResponse(
                result=ActionResult.INVALID_ACTION,
                message="No turn in progress."
            )
        
        previous_player = self._game.current_player.name
        self._turn_manager.end_turn()
        self._turn_started = False
        
        self._notify_state_change()
        
        return ActionResponse(
            result=ActionResult.SUCCESS,
            message=f"{previous_player}'s turn force-ended. Next: {self._game.current_player.name}",
            game_state_changed=True
        )
    
    # =============================
    # Action Queries (for UI)
    # =============================
    
    def get_available_actions(self) -> List[Action]:
        """
        Get all available actions for the current player.
        
        The UI should call this to know what actions to display.
        
        Returns:
            List of legal Action objects
        """
        if not self._turn_started:
            return []
        
        if self._turn_manager.actions_remaining <= 0:
            return []
        
        return self._rules_engine.get_legal_actions(self._game.current_player)
    
    def get_available_actions_by_type(self, action_type: ActionType) -> List[Action]:
        """
        Get available actions filtered by type.
        
        Args:
            action_type: The type of action to filter by
            
        Returns:
            List of legal actions of the specified type
        """
        if not self._turn_started:
            return []
        
        return self._rules_engine.get_legal_actions_by_type(
            self._game.current_player, action_type
        )
    
    def get_action_count(self) -> Dict[str, int]:
        """
        Get count of available actions by type.
        
        Returns:
            Dictionary mapping action type names to counts
        """
        actions = self.get_available_actions()
        counts: Dict[str, int] = {}
        for action in actions:
            type_name = action.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def has_available_actions(self) -> bool:
        """
        Check if current player has any available actions.
        
        Returns:
            True if at least one action is available
        """
        return len(self.get_available_actions()) > 0
    
    # =============================
    # Action Submission (from UI)
    # =============================
    
    def submit_action(self, action: Action, extra_context: Optional[Dict[str, Any]] = None) -> ActionResponse:
        """
        Submit an action to be executed.
        
        This is the main entry point for the UI to execute player actions.
        The controller validates the action and executes it if legal.
        
        Args:
            action: The Action object to execute
            extra_context: Additional context for tile effects (e.g., depot choices)
            
        Returns:
            ActionResponse with result status and details
        """
        if extra_context is None:
            extra_context = {}
        
        # Validate turn state
        if not self._turn_started:
            return ActionResponse(
                result=ActionResult.NOT_YOUR_TURN,
                message="Turn has not started. Call start_turn() first.",
                action=action
            )
        
        if self._turn_manager.actions_remaining <= 0:
            return ActionResponse(
                result=ActionResult.NO_ACTIONS_REMAINING,
                message="No actions remaining this turn.",
                action=action
            )
        
        player = self._game.current_player
        
        # Validate action is legal
        if not self._rules_engine.is_action_legal(player, action):
            return ActionResponse(
                result=ActionResult.ILLEGAL_MOVE,
                message=f"Action '{action.description}' is not legal.",
                action=action
            )
        
        # Execute the action
        try:
            result = self._execute_action(player, action, extra_context)
            return result
        except ValueError as e:
            return ActionResponse(
                result=ActionResult.INSUFFICIENT_RESOURCES,
                message=str(e),
                action=action
            )
        except Exception as e:
            return ActionResponse(
                result=ActionResult.INVALID_ACTION,
                message=f"Error executing action: {str(e)}",
                action=action
            )
    
    def _execute_action(
        self, 
        player: Player, 
        action: Action, 
        extra_context: Dict[str, Any]
    ) -> ActionResponse:
        """
        Execute a validated action.
        
        Args:
            player: The player executing the action
            action: The action to execute
            extra_context: Additional context for complex actions
            
        Returns:
            ActionResponse with execution result
        """
        extra_data: Dict[str, Any] = {}
        
        if action.type == ActionType.TAKE_TILE:
            depot_id = action.params["depot_id"]
            die_value = action.params.get("die_value", 0)
            workers_cost = action.cost.get("workers", 0)
            
            # Spend workers if needed
            if workers_cost > 0:
                player.spend_workers(workers_cost)
            
            # Take the tile
            self._game.action_take_hex_from_depot(depot_id)
            
            # Use the die
            if die_value in player.dice:
                player.use_die(die_value)
            
            extra_data["depot_id"] = depot_id
            extra_data["tile_taken"] = player.hex_storage[-1].tile_type.name
            message = f"Took {extra_data['tile_taken']} from depot {depot_id}"
        
        elif action.type == ActionType.PLACE_TILE:
            storage_index = action.params["storage_index"]
            coord = action.params["coord"]
            die_value = action.params.get("die_value", 0)
            workers_cost = action.cost.get("workers", 0)
            
            # Spend workers if needed
            if workers_cost > 0:
                player.spend_workers(workers_cost)
            
            # Place the tile
            # on utilise un dico vide qui sera remplie par _apply_castle_effect
            ctx = extra_context.copy()
            result = self._game.action_place_tile_from_storage(
                storage_index, coord, self._game.global_round, ctx
            )
            
            # Use the die
            if die_value in player.dice:
                player.use_die(die_value)
            
            # un chateau donne un extra action
            if ctx.get("castle_bonus_action_available"):
                # On recrédite une action (ou on n'en consomme pas)
                # Ici, comme on va faire use_action() à la fin, on en ajoute une pour compenser
                self._turn_manager.actions_remaining += 1
                message = f"Placed Castle at {coord} (Bonus Action!)"
            else:
                message = f"Placed tile at {coord}"

            extra_data["placement_result"] = result
        
        elif action.type == ActionType.SELL_GOODS:
            color_name = action.params["color"]
            die_value = action.params.get("die_value", 0)
            
            # Find the color enum
            color = None
            for c in GoodsColor:
                if c.name == color_name:
                    color = c
                    break
            
            if color is None:
                raise ValueError(f"Unknown goods color: {color_name}")
            
            # Sell the goods
            sold_count = player.sell_goods_of_color(color)
            
            # Use the die
            if die_value in player.dice:
                player.use_die(die_value)
            
            extra_data["color"] = color_name
            extra_data["sold_count"] = sold_count
            extra_data["silverlings_gained"] = sold_count * player.get_silverlings_per_good_sold()
            message = f"Sold {sold_count} {color_name} goods"
        
        elif action.type == ActionType.TAKE_WORKERS:
            die_value = action.params.get("die_value", 0)
            workers_gained = player.get_workers_from_take_action()
            silverling_bonus = player.get_silverling_bonus_on_take_workers()
            
            # Gain workers
            player.gain_workers(workers_gained)
            
            # Gain silverling bonus if applicable
            if silverling_bonus > 0:
                player.gain_silverlings(silverling_bonus)
            
            # Use the die
            if die_value in player.dice:
                player.use_die(die_value)
            
            extra_data["workers_gained"] = workers_gained
            extra_data["silverling_bonus"] = silverling_bonus
            message = f"Took {workers_gained} workers"
        
        elif action.type == ActionType.BUY_BLACK_TILE:
            # Buy from black depot (costs 2 silverlings)
            self._game.action_take_hex_from_black_depot()
            
            extra_data["tile_taken"] = player.hex_storage[-1].tile_type.name
            message = f"Bought {extra_data['tile_taken']} from black depot"
        
        elif action.type == ActionType.DISCARD_TILE:
            storage_index = action.params["storage_index"]
            tile_type = action.params.get("tile_type", "tile")
            
            # Remove the tile (discard it)
            player.remove_hex_from_storage(storage_index)
            
            extra_data["discarded_tile"] = tile_type
            message = f"Discarded {tile_type} from storage"
            
            # Discard is a free action, don't consume turn action
            self._notify_state_change()
            return ActionResponse(
                result=ActionResult.SUCCESS,
                message=message,
                action=action,
                game_state_changed=True,
                extra_data=extra_data
            )
        
        else:
            raise ValueError(f"Unknown action type: {action.type}")
        
        # Consume a turn action (except for free actions like discard)
        self._turn_manager.use_action()
        
        # Notify observers
        self._notify_state_change()
        
        return ActionResponse(
            result=ActionResult.SUCCESS,
            message=message,
            action=action,
            game_state_changed=True,
            extra_data=extra_data
        )
    
    # =============================
    # Game State Queries (for UI)
    # =============================
    
    def get_game_state(self) -> GameStateView:
        """
        Get an immutable view of the current game state.
        
        This is safe for the UI to use without risk of modifying game state.
        
        Returns:
            GameStateView with current game information
        """
        player = self._game.current_player
        
        # Build player summaries
        summaries = []
        for p in self._game.players:
            summaries.append({
                "name": p.name,
                "victory_points": p.victory_points,
                "silverlings": p.silverlings,
                "workers": p.workers,
                "hex_storage_count": len(p.hex_storage),
                "goods_count": len(p.goods_storage),
                "yellow_tiles_count": len(p.yellow_effects)
            })
        
        return GameStateView(
            current_player_name=player.name,
            current_player_index=self._game.current_player_index,
            current_phase=self._game.board.current_phase,
            round_in_phase=self._game.board.round_in_phase,
            global_round=self._game.global_round,
            dice=tuple(player.dice),
            silverlings=player.silverlings,
            workers=player.workers,
            victory_points=player.victory_points,
            hex_storage_count=len(player.hex_storage),
            goods_count=len(player.goods_storage),
            actions_remaining=self._turn_manager.actions_remaining,
            is_game_over=False,  # TODO: Implement game over detection
            player_summaries=tuple(summaries)
        )
    
    def get_current_player_name(self) -> str:
        """Get the name of the current player."""
        return self._game.current_player.name
    
    def get_actions_remaining(self) -> int:
        """Get the number of actions remaining this turn."""
        return self._turn_manager.actions_remaining
    
    def is_turn_active(self) -> bool:
        """Check if a turn is currently in progress."""
        return self._turn_started
    
    def get_current_dice(self) -> List[int]:
        """Get the current player's dice values."""
        return self._game.current_player.dice.copy()
    
    # =============================
    # Board State Queries (for UI)
    # =============================
    
    def get_depot_contents(self, depot_id: int) -> List[str]:
        """
        Get the tile types in a depot.
        
        Args:
            depot_id: The depot number (1-6)
            
        Returns:
            List of tile type names
        """
        if depot_id not in self._game.board.depots:
            return []
        return [t.tile_type.name for t in self._game.board.depots[depot_id]]
    
    def get_all_depot_contents(self) -> Dict[int, List[str]]:
        """
        Get contents of all depots.
        
        Returns:
            Dictionary mapping depot IDs to lists of tile type names
        """
        return {i: self.get_depot_contents(i) for i in range(1, 7)}
    
    def get_black_depot_contents(self) -> List[str]:
        """Get the tile types in the black depot."""
        return [t.tile_type.name for t in self._game.board.black_depot]
    
    def get_depot_goods(self, depot_id: int) -> List[str]:
        """
        Get the goods in a depot.
        
        Args:
            depot_id: The depot number (1-6)
            
        Returns:
            List of goods color names
        """
        if depot_id not in self._game.board.depot_goods:
            return []
        return [g.color.name for g in self._game.board.depot_goods[depot_id]]
    
    # =============================
    # Observer Pattern (for UI updates)
    # =============================
    
    def register_state_change_callback(self, callback: Callable[[GameStateView], None]) -> None:
        """
        Register a callback to be notified when game state changes.
        
        Args:
            callback: Function to call with the new GameStateView
        """
        self._state_change_callbacks.append(callback)
    
    def unregister_state_change_callback(self, callback: Callable[[GameStateView], None]) -> None:
        """
        Unregister a state change callback.
        
        Args:
            callback: The callback to remove
        """
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)
    
    def _notify_state_change(self) -> None:
        """Notify all registered callbacks of a state change."""
        state = self.get_game_state()
        for callback in self._state_change_callbacks:
            callback(state)


# ============================================================================
# EXAMPLE USAGE - Demonstrates UI -> Controller -> Game flow
# ============================================================================

if __name__ == "__main__":
    """
    Example demonstrating clean architecture with GameController.
    
    This simulates how a UI would interact with the controller:
    1. Query available actions
    2. Display them (simulated with print)
    3. Select an action (simulated with code)
    4. Submit to controller
    5. Handle response
    """
    
    from board import Tile, GoodsTile
    
    print("=" * 70)
    print("GAME CONTROLLER - CLEAN ARCHITECTURE EXAMPLE")
    print("=" * 70)
    
    # =====================
    # SETUP: Create game and controller
    # =====================
    print("\n--- SETUP ---")
    
    game = Game(player_names=["Alice", "Bob"], seed=42)
    controller = GameController(game)
    
    print(f"Game created with players: {[p.name for p in game.players]}")
    print("Controller initialized")
    
    # Register a state change observer (simulating UI update handler)
    def on_state_change(state: GameStateView):
        print(f"  [UI UPDATE] State changed - {state.current_player_name}'s turn, "
              f"{state.actions_remaining} actions left")
    
    controller.register_state_change_callback(on_state_change)
    
    # =====================
    # EXAMPLE 1: Starting a turn
    # =====================
    print("\n--- EXAMPLE 1: Starting a Turn ---")
    
    # UI calls controller to start turn
    response = controller.start_turn()
    print(f"Start turn response: {response.result.name}")
    print(f"Message: {response.message}")
    
    # UI queries game state
    state = controller.get_game_state()
    print("\nGame state view:")
    print(f"  Current player: {state.current_player_name}")
    print(f"  Dice: {state.dice}")
    print(f"  Actions remaining: {state.actions_remaining}")
    
    # =====================
    # EXAMPLE 2: Querying available actions
    # =====================
    print("\n--- EXAMPLE 2: Querying Available Actions ---")
    
    # UI asks controller for available actions
    available_actions = controller.get_available_actions()
    action_counts = controller.get_action_count()
    
    print(f"Total available actions: {len(available_actions)}")
    print(f"Actions by type: {action_counts}")
    
    print("\nAction list (as UI would display):")
    for i, action in enumerate(available_actions):
        print(f"  [{i}] {action.type.value}: {action.description}")
    
    # =====================
    # EXAMPLE 3: Submitting an action (Take Tile)
    # =====================
    print("\n--- EXAMPLE 3: Submitting an Action ---")
    
    # Give player some workers for the demo
    game.current_player.gain_workers(3)
    
    # UI selects an action (simulated - in real UI, user would click)
    take_tile_actions = controller.get_available_actions_by_type(ActionType.TAKE_TILE)
    
    if take_tile_actions:
        # User chooses first take tile action
        chosen_action = take_tile_actions[0]
        print(f"User selected: {chosen_action.description}")
        
        # UI submits action to controller
        response = controller.submit_action(chosen_action)
        
        print("\nController response:")
        print(f"  Result: {response.result.name}")
        print(f"  Message: {response.message}")
        print(f"  State changed: {response.game_state_changed}")
        if response.extra_data:
            print(f"  Extra data: {response.extra_data}")
    
    # =====================
    # EXAMPLE 4: Checking updated state
    # =====================
    print("\n--- EXAMPLE 4: Updated State ---")
    
    state = controller.get_game_state()
    print("After action:")
    print(f"  Dice remaining: {state.dice}")
    print(f"  Actions remaining: {state.actions_remaining}")
    print(f"  Hex storage: {state.hex_storage_count} tiles")
    
    # =====================
    # EXAMPLE 5: Completing the turn
    # =====================
    print("\n--- EXAMPLE 5: Completing the Turn ---")
    
    # Perform second action (take workers)
    worker_actions = controller.get_available_actions_by_type(ActionType.TAKE_WORKERS)
    if worker_actions:
        response = controller.submit_action(worker_actions[0])
        print(f"Second action: {response.message}")
    
    # Check if turn is complete
    print(f"\nTurn complete: {controller.get_actions_remaining() == 0}")
    
    # End the turn
    if controller.get_actions_remaining() == 0:
        response = controller.end_turn()
        print(f"End turn: {response.message}")
    
    # =====================
    # EXAMPLE 6: Illegal action handling
    # =====================
    print("\n--- EXAMPLE 6: Illegal Action Handling ---")
    
    # Start new player's turn
    controller.start_turn()
    
    # Try to submit an action that doesn't exist in available actions
    fake_action = Action(
        type=ActionType.TAKE_TILE,
        params={"depot_id": 99},  # Invalid depot
        description="Invalid action"
    )
    
    response = controller.submit_action(fake_action)
    print("Illegal action response:")
    print(f"  Result: {response.result.name}")
    print(f"  Message: {response.message}")
    
    # =====================
    # EXAMPLE 7: Board state queries
    # =====================
    print("\n--- EXAMPLE 7: Board State Queries ---")
    
    print("Depot contents:")
    all_depots = controller.get_all_depot_contents()
    for depot_id, tiles in all_depots.items():
        print(f"  Depot {depot_id}: {tiles}")
    
    print(f"\nBlack depot: {controller.get_black_depot_contents()[:5]}...")
    
    # =====================
    # EXAMPLE 8: Full turn simulation with UI-like flow
    # =====================
    print("\n--- EXAMPLE 8: Full Turn Simulation ---")
    
    # Force end current turn to start fresh
    controller.force_end_turn()
    
    # Simulate a complete turn with UI-like flow
    print("\n[UI] Starting turn...")
    controller.start_turn()
    
    state = controller.get_game_state()
    print(f"[UI] It's {state.current_player_name}'s turn")
    print(f"[UI] Dice rolled: {state.dice}")
    
    # Action 1
    actions = controller.get_available_actions()
    print(f"[UI] Displaying {len(actions)} available actions...")
    
    if actions:
        # Simulate user clicking on first action
        selected = actions[0]
        print(f"[UI] User clicked: {selected.description}")
        
        response = controller.submit_action(selected)
        if response.result == ActionResult.SUCCESS:
            print(f"[UI] Action successful: {response.message}")
        else:
            print(f"[UI] Action failed: {response.message}")
    
    # Action 2
    actions = controller.get_available_actions()
    if actions:
        selected = actions[0]
        print(f"[UI] User clicked: {selected.description}")
        
        response = controller.submit_action(selected)
        if response.result == ActionResult.SUCCESS:
            print(f"[UI] Action successful: {response.message}")
    
    # End turn
    if controller.get_actions_remaining() == 0:
        print("[UI] No actions remaining, ending turn...")
        controller.end_turn()
        print(f"[UI] Next player: {controller.get_current_player_name()}")
    
    # =====================
    # SUMMARY
    # =====================
    print("\n" + "=" * 70)
    print("ARCHITECTURE SUMMARY")
    print("=" * 70)
    print("""
Clean Architecture Layers:

1. UI LAYER (not implemented - simulated above)
   - Detects user input (clicks, selections)
   - Queries controller for available actions
   - Displays actions to user
   - Submits chosen Action to controller
   - NEVER modifies game state directly

2. CONTROLLER LAYER (GameController)
   - Exposes available actions via get_available_actions()
   - Validates actions via RulesEngine
   - Executes actions through Game methods
   - Returns ActionResponse with results
   - Manages turn state via TurnManager
   - Provides read-only GameStateView

3. GAME LAYER (Game, Player, Board)
   - Contains all game logic
   - No knowledge of UI
   - No knowledge of Controller
   - Pure domain logic

Key Design Principles:
- Dependency flows inward (UI -> Controller -> Game)
- Game layer has no external dependencies
- Controller is UI-agnostic
- Actions are immutable value objects
- State changes flow through controller only
""")
    print("=" * 70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("=" * 70)
