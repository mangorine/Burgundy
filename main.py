# ui/main.py
import pygame
import time

from game import Game
from board import TileType, Tile, PlayerBoard
from render_hex import draw_player_board, draw_storage, pixel_to_axial
from render_central import (
    draw_central_board,
    draw_steps,
    DEPOT_HEXES,
    BLACK_DEPOT_RECT,
    DEPOT_HEIGHT,
)
from colors import BACKGROUND_COLOR
from render_ui import draw_button, draw_panel, draw_die, draw_toast

# ===============================
# INIT
# ===============================
pygame.init()
pygame.font.init()

FONT = pygame.font.SysFont(None, 28)
FONT_SMALL = pygame.font.SysFont(None, 22)
FONT_BIG = pygame.font.SysFont(None, 36)

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Castles of Burgundy")
clock = pygame.time.Clock()

PLAYER_COLORS = [
    (235, 80, 80),
    (80, 160, 235),
    (80, 200, 120),
    (235, 180, 80),
]

# ===============================
# MODES
# ===============================
MODE_MENU = "menu"
MODE_GAME = "game"
VIEW_CENTRAL = "central"
VIEW_PLAYER = "player"

mode = MODE_MENU
current_view = VIEW_CENTRAL

# ===============================
# GAME STATE
# ===============================
game: Game | None = None
current_player_index = 0

selected_layout_id = 1
selected_central_tile = None

selected_tile = None
selected_storage_index = None
selected_hex = None
legal_coords = set()

BOARD_ORIGIN = (WIDTH // 2, HEIGHT // 2)

# ===============================
# UI RECTS
# ===============================
PLAYER_BUTTONS = [pygame.Rect(40 + i * 120, HEIGHT - 70, 100, 36) for i in range(4)]
BACK_BUTTON = pygame.Rect(20, 20, 180, 36)

# HUD EN BAS À DROITE
HUD_RECT = pygame.Rect(WIDTH - 320, HEIGHT - 260, 300, 240)
ROLL_BTN = pygame.Rect(HUD_RECT.x + 20, HUD_RECT.y + 180, 120, 40)
ENDTURN_BTN = pygame.Rect(HUD_RECT.x + 160, HUD_RECT.y + 180, 120, 40)

TOAST_RECT = pygame.Rect(20, 20, 520, 46)
toast_message = ""
toast_until = 0.0

dice_a = 1
dice_b = 1
white_die = 1

# ===============================
# HELPERS
# ===============================
def toast(msg, seconds=2.5):
    global toast_message, toast_until
    toast_message = msg
    toast_until = time.time() + seconds
    print("[UI]", msg)


def reset_player_view_state():
    global selected_tile, selected_storage_index, selected_hex
    selected_tile = None
    selected_storage_index = None
    selected_hex = None
    legal_coords.clear()


def set_active_player(index):
    global current_player_index
    current_player_index = index
    for i, p in enumerate(game.players):
        p.is_active = (i == index)


def actions_left():
    return len(game.current_player.dice)


def require_roll_and_actions():
    if not game.current_player.dice:
        toast("Lance les dés d'abord (Roll / R)")
        return False
    return True


def ui_roll():
    player = game.current_player
    if player.dice:
        toast("Déjà lancé")
        return
    player.roll_dice()
    global dice_a, dice_b
    dice_a, dice_b = player.dice
    toast(f"Dés: {dice_a}, {dice_b}")


def end_turn():
    global selected_central_tile, current_view, dice_a, dice_b

    game.current_player.dice.clear()
    game.next_player()
    set_active_player(game.current_player_index)

    selected_central_tile = None
    reset_player_view_state()
    current_view = VIEW_CENTRAL

    dice_a, dice_b = 1, 1
    toast(f"Tour → {game.current_player.name}")

# ===============================
# MAIN LOOP
# ===============================
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ===== MENU =====
        if mode == MODE_MENU and event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                selected_layout_id = event.key - pygame.K_0
                toast(f"Layout {selected_layout_id}")

            if event.key == pygame.K_RETURN:
                game = Game(["Player 1", "Player 2", "Player 3", "Player 4"])
                for i, p in enumerate(game.players):
                    p.board = PlayerBoard(layout_id=selected_layout_id)
                    p.color = PLAYER_COLORS[i]
                    p.step_position = 1
                    p.is_active = False
                    p.silverlings = 5

                set_active_player(0)
                reset_player_view_state()
                current_view = VIEW_CENTRAL
                mode = MODE_GAME
                toast("Partie lancée")
            continue

        # ===== CLAVIER =====
        if mode == MODE_GAME and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_view = VIEW_CENTRAL
                reset_player_view_state()

            if event.key == pygame.K_r:
                ui_roll()

            if event.key == pygame.K_SPACE:
                end_turn()

        # ===== SOURIS =====
        if mode == MODE_GAME and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            active = game.current_player

            # --- HUD ---
            if HUD_RECT.collidepoint(mx, my):
                if ROLL_BTN.collidepoint(mx, my):
                    ui_roll()
                elif ENDTURN_BTN.collidepoint(mx, my):
                    end_turn()
                continue

            # --- VUE CENTRALE ---
            if current_view == VIEW_CENTRAL:
                # Dépôts normaux
                for (depot_id, idx), data in list(DEPOT_HEXES.items()):
                    if data["rect"].collidepoint(mx, my):
                        if not require_roll_and_actions():
                            break
                        try:
                            game.action_take_hex_from_depot(depot_id)
                            die_used = active.dice[0]
                            active.use_die(die_used)
                            toast(f"Tuile prise (dé {die_used})")
                        except Exception as e:
                            toast(str(e))
                        break

                # Dépôt noir
                if BLACK_DEPOT_RECT and BLACK_DEPOT_RECT.collidepoint(mx, my):
                    if not require_roll_and_actions():
                        continue
                    try:
                        game.action_take_hex_from_black_depot()
                        die_used = active.dice[0]
                        active.use_die(die_used)
                        toast("Tuile noire achetée")
                    except Exception as e:
                        toast(str(e))

                # Boutons joueurs
                for i, rect in enumerate(PLAYER_BUTTONS):
                    if rect.collidepoint(mx, my):
                        set_active_player(i)
                        current_view = VIEW_PLAYER
                        reset_player_view_state()

            # --- VUE JOUEUR ---
            elif current_view == VIEW_PLAYER:
                if BACK_BUTTON.collidepoint(mx, my):
                    current_view = VIEW_CENTRAL
                    reset_player_view_state()
                    continue

                player = game.current_player
                coord = pixel_to_axial(mx, my, BOARD_ORIGIN)

                if coord in player.board.hex_map.grid:
                    selected_hex = coord

                if selected_tile is not None and selected_storage_index is not None:
                    if coord in legal_coords and require_roll_and_actions():
                        slot = player.board.hex_map.get_slot(coord)
                        die_val = slot.dice_value
                        try:
                            game.action_place_tile_from_storage(
                                selected_storage_index,
                                coord,
                                game.global_round,
                                die_val,
                            )
                            toast("Tuile posée")
                        except Exception as e:
                            toast(str(e))
                        reset_player_view_state()

                sx, sy = WIDTH // 2 - 90, HEIGHT - 120
                for i in range(3):
                    rect = pygame.Rect(sx + i * 70, sy, 50, 50)
                    if rect.collidepoint(mx, my) and i < len(player.hex_storage):
                        selected_storage_index = i
                        selected_tile = player.hex_storage[i]

    # ===== LOGIQUE =====
    if mode == MODE_GAME and current_view == VIEW_PLAYER and selected_tile:
        player = game.current_player
        legal_coords.clear()
        for c in player.board.hex_map.grid:
            can_place, _, _ = player.can_use_die_for_placement(c)
            if can_place:
                legal_coords.add(c)

    # ===== RENDU =====
    screen.fill(BACKGROUND_COLOR)
    mx, my = pygame.mouse.get_pos()

    if mode == MODE_MENU:
        screen.blit(
            FONT_BIG.render("Choisis un layout (1–9) puis ENTER", True, (255, 255, 255)),
            (WIDTH // 2 - 260, HEIGHT // 2 - 30),
        )

    elif mode == MODE_GAME:
        if toast_message and time.time() < toast_until:
            draw_toast(screen, TOAST_RECT, toast_message, FONT)

        if current_view == VIEW_CENTRAL:
            draw_central_board(screen, game.board, (100, 100), (mx, my), selected_central_tile)
            draw_steps(screen, game.players, (150, 100 + DEPOT_HEIGHT + 140))

            for i, rect in enumerate(PLAYER_BUTTONS):
                pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=8)
                if i == current_player_index:
                    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
                txt = FONT.render(f"Joueur {i+1}", True, (255, 255, 255))
                screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

            draw_panel(screen, HUD_RECT)
            p = game.current_player
            screen.blit(FONT_SMALL.render(f"Joueur: {p.name}", True, (230, 230, 230)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 12))
            screen.blit(FONT_SMALL.render(f"Argent: {p.silverlings}", True, (200, 200, 200)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 34))
            screen.blit(FONT_SMALL.render(f"Actions: {actions_left()}", True, (200, 200, 200)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 56))

            draw_die(screen, (HUD_RECT.x + 70, HUD_RECT.y + 110), dice_a, FONT)
            draw_die(screen, (HUD_RECT.x + 150, HUD_RECT.y + 110), dice_b, FONT)

            draw_button(screen, ROLL_BTN, "Roll (R)", FONT_SMALL)
            draw_button(screen, ENDTURN_BTN, "Fin tour", FONT_SMALL)

        else:
            player = game.current_player
            draw_player_board(screen, player.board, BOARD_ORIGIN, selected_hex, legal_coords)
            draw_storage(screen, player.hex_storage, selected_storage_index,
                         (WIDTH // 2 - 90, HEIGHT - 120))

            pygame.draw.rect(screen, (60, 60, 60), BACK_BUTTON, border_radius=8)
            pygame.draw.rect(screen, (200, 200, 200), BACK_BUTTON, 2, border_radius=8)
            screen.blit(FONT.render("← Plateau central", True, (255, 255, 255)),
                        (BACK_BUTTON.x + 12, BACK_BUTTON.y + 8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
