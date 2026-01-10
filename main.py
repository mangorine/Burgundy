# ui/main.py
import pygame

from game import Game
from board import TileType, Tile, PlayerBoard
from render_hex import draw_player_board, draw_storage, pixel_to_axial
from colors import BACKGROUND_COLOR

# ===============================
# INIT PYGAME
# ===============================
pygame.init()
pygame.font.init()
FONT_TILE = pygame.font.SysFont(None, 28)
VIEW_CENTRAL = "central"
VIEW_PLAYER = "player"

current_view = VIEW_CENTRAL
current_player_index = 0
current_player_view=None

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Castles of Burgundy - GUI")
clock = pygame.time.Clock()

# ===============================
# MODESa
# ===============================
MODE_MENU = "menu"
MODE_GAME = "game"
mode = MODE_MENU

# ===============================
# ÉTAT GLOBAL GUI
# ===============================
selected_layout_id = 1

game = None
player = None

selected_tile = None
selected_storage_index = None
selected_hex = None
legal_coords = set()

pending_choice = None  # dict ou None

BOARD_ORIGIN = (WIDTH // 2, HEIGHT // 2)

PLAYER_BUTTONS = []
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 40
BUTTON_GAP = 10

def build_player_buttons(num_players):
    buttons = []
    start_x = WIDTH // 2 - (num_players * (BUTTON_WIDTH + BUTTON_GAP)) // 2
    y = 20

    for i in range(num_players):
        rect = pygame.Rect(
            start_x + i * (BUTTON_WIDTH + BUTTON_GAP),
            y,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )
        buttons.append(rect)

    return buttons

def ask_number_choice(choice_type, min_val, max_val, callback):
    global pending_choice
    pending_choice = {
        "type": choice_type,
        "min": min_val,
        "max": max_val,
        "callback": callback,
    }
    print(f"Choix requis ({choice_type}) : {min_val} à {max_val}")


# ===============================
# BOUCLE PRINCIPALE
# ===============================
running = True
while running:

    # ===============================
    # 1️ EVENTS
    # ===============================
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ===============================
        # MODE MENU
        # ===============================
        if mode == MODE_MENU:

            if event.type == pygame.KEYDOWN:

                if pygame.K_1 <= event.key <= pygame.K_9:
                    selected_layout_id = event.key - pygame.K_0
                    print(f"Layout sélectionné : {selected_layout_id}")

                if event.key == pygame.K_RETURN:
                    if event.key == pygame.K_RETURN:
                        game = Game(["Player 1", "Player 2","Player3","Player4"]) 
                        player = game.current_player
                        player.board = PlayerBoard(layout_id=selected_layout_id)

                        PLAYER_BUTTONS = build_player_buttons(len(game.players))

                        current_view = VIEW_CENTRAL
                        mode = MODE_GAME

                    # DEBUG : tuile test
                    player.add_hex_to_storage(Tile(TileType.BUILDING))

                    # === TEST CHOIX CLAVIER ===
                    def test_callback(x):
                        print("Choix reçu :", x)

                    ask_number_choice("depot", 1, 6, test_callback)

                    selected_tile = None
                    selected_storage_index = None
                    selected_hex = None
                    legal_coords.clear()

                    mode = MODE_GAME
                    print("Partie lancée")

            continue

        # ===============================
        # MODE GAME
        # ===============================
        if mode == MODE_GAME:

            # ----- CHOIX CLAVIER PRIORITAIRE -----
            if pending_choice and event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    value = event.key - pygame.K_0

                    if pending_choice["min"] <= value <= pending_choice["max"]:
                        callback = pending_choice["callback"]
                        pending_choice = None
                        callback(value)
                    else:
                        print("Choix invalide")

                continue

            # ----- SOURIS -----
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if current_view == VIEW_CENTRAL:
                    for i, rect in enumerate(PLAYER_BUTTONS):
                         if rect.collidepoint(mx, my):
                                current_player_index = i
                                current_view = VIEW_PLAYER
                                selected_tile = None
                                selected_hex=None
                                selected_storage_index = None
                                legal_coords.clear()
                                print(f"Vue joueur {i + 1}")
                                break
                
                elif current_view == VIEW_PLAYER:           
                    player = game.players[current_player_index]
                    coord = pixel_to_axial(mx, my, BOARD_ORIGIN)

                    if coord in player.board.hex_map.grid:
                        selected_hex = coord

                    if (
                        selected_tile is not None
                        and selected_storage_index is not None
                        and coord in legal_coords
                    ):
                        result = game.action_place_tile_from_storage(
                            selected_storage_index,
                            coord,
                            game.global_round,
                            extra_context={},
                        )

                        selected_tile = None
                        selected_storage_index = None
                        selected_hex = None
                        legal_coords.clear()

                        print("Placement effectué :", result)

                    # stockage
                    storage_origin = (WIDTH // 2 - 90, HEIGHT - 120)
                    SLOT_SIZE = 50
                    GAP = 20

                    for i in range(3):
                        rect = pygame.Rect(
                            storage_origin[0] + i * (SLOT_SIZE + GAP),
                            storage_origin[1],
                            SLOT_SIZE,
                            SLOT_SIZE,
                        )

                        if rect.collidepoint(mx, my):
                            if i < len(player.hex_storage):
                                selected_storage_index = i
                                selected_tile = player.hex_storage[i]
                            else:
                                selected_storage_index = None
                                selected_tile = None
                            break
    # ===============================
    # 2️ LOGIQUE GUI
    # ===============================
    
    if mode == MODE_GAME and current_view==VIEW_PLAYER:
            legal_coords.clear()
            if selected_tile:
                player = game.players[current_player_index]
                for coord in player.board.hex_map.grid:
                    if player.board.can_place_tile_at(selected_tile, coord, player):
                        legal_coords.add(coord)
       
    # ===============================
    # 3️ RENDU
    # ===============================
    if mode == MODE_MENU:
        screen.fill((30, 30, 30))

        screen.blit(
            FONT_TILE.render("Choisis un layout (1–9)", True, (255, 255, 255)),
            (WIDTH // 2 - 140, HEIGHT // 2 - 60),
        )
        screen.blit(
            FONT_TILE.render(
                f"Layout sélectionné : {selected_layout_id}", True, (200, 200, 200)
            ),
            (WIDTH // 2 - 140, HEIGHT // 2),
        )
        screen.blit(
            FONT_TILE.render("Appuie sur ENTREE pour lancer", True, (180, 180, 180)),
            (WIDTH // 2 - 160, HEIGHT // 2 + 40),
        )

    elif mode == MODE_GAME:
        screen.fill(BACKGROUND_COLOR)

        draw_player_board(
            screen, player.board, BOARD_ORIGIN, selected_hex, legal_coords
        )
        draw_storage(
            screen,
            player.hex_storage,
            selected_storage_index,
            (WIDTH // 2 - 90, HEIGHT - 120),
        )

        if pending_choice:
            screen.blit(
                FONT_TILE.render(
                    f"Choix requis : {pending_choice['type']} ({pending_choice['min']}–{pending_choice['max']})",
                    True,
                    (255, 220, 120),
                ),
                (20, 20),
            )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
