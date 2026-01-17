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
    STEP_RECTS,
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
# MODES / VUES
# ===============================
MODE_MENU = "menu"
MODE_GAME = "game"
VIEW_CENTRAL = "central"
VIEW_PLAYER = "player"

mode = MODE_MENU
current_view = VIEW_CENTRAL
current_player_index = 0

# ===============================
# ÉTAT GLOBAL
# ===============================
selected_layout_id = 1
selected_central_tile = None

game = None

selected_tile = None
selected_storage_index = None
selected_hex = None
legal_coords = set()

BOARD_ORIGIN = (WIDTH // 2, HEIGHT // 2)

# ===============================
# UI
# ===============================
PLAYER_BUTTONS = [
    pygame.Rect(50 + i * 120, HEIGHT - 70, 100, 40) for i in range(4)
]
BACK_BUTTON = pygame.Rect(20, 20, 180, 40)

# HUD EN BAS À DROITE
HUD_RECT = pygame.Rect(WIDTH - 320, HEIGHT - 240, 300, 220)
ROLL_BTN = pygame.Rect(HUD_RECT.x + 20, HUD_RECT.y + 160, 120, 40)
ENDTURN_BTN = pygame.Rect(HUD_RECT.x + 160, HUD_RECT.y + 160, 120, 40)

TOAST_RECT = pygame.Rect(20, 20, 520, 46)
toast_message = ""
toast_until = 0.0

# Dés affichés
dice_a = None
dice_b = None
white_die = None

# ✅ Sélection du dé (nouveau)
selected_die = None
DIE_RECTS = {}  # value -> rect cliquable (on les remplit au rendu)

# ===============================
# HELPERS
# ===============================
def toast(msg, seconds=2.5):
    global toast_message, toast_until
    toast_message = msg
    toast_until = time.time() + seconds
    print("[UI]", msg)


def reset_player_view_state():
    global selected_tile, selected_storage_index, selected_hex, selected_central_tile
    selected_tile = None
    selected_storage_index = None
    selected_hex = None
    selected_central_tile = None
    legal_coords.clear()


def set_active_player(index):
    global current_player_index
    current_player_index = index
    for p in game.players:
        p.is_active = False
    game.players[index].is_active = True


def current_player():
    return game.players[current_player_index]


def ensure_rolled():
    p = current_player()
    if not getattr(p, "dice", None) or len(p.dice) == 0:
        toast("Lance d'abord les dés (Roll).")
        return False
    return True


def ensure_selected_die():
    if selected_die is None:
        toast("Clique sur un dé d'abord.")
        return False
    p = current_player()
    if selected_die not in p.dice:
        toast("Ce dé n'est plus disponible.")
        return False
    return True


def clear_dice_ui():
    global dice_a, dice_b, selected_die
    dice_a = None
    dice_b = None
    selected_die = None
    DIE_RECTS.clear()


def end_turn():
    # passe joueur suivant (dans game.py : next_player)
    game.next_player()
    set_active_player(game.current_player_index)

    # on force le prochain joueur à relancer
    p = current_player()
    p.dice = []

    clear_dice_ui()
    reset_player_view_state()
    toast("Tour suivant")


def try_take_from_depot(depot_id: int):
    """
    Prise tuile dépôt en respectant :
    - dé sélectionné obligatoire
    - workers si ajustement nécessaire
    - consomme le dé sélectionné
    - appelle game.action_take_hex_from_depot(depot_id) (sans changer game.py)
    """
    global selected_die

    p = current_player()

    if not ensure_rolled() or not ensure_selected_die():
        return

    # Peut-on atteindre depot_id avec CE dé sélectionné ?
    # => utilise ta logique Player.py (ajustement + wrap)
    can_reach, workers_needed = p.can_reach_value_with_workers(depot_id, selected_die)

    if not can_reach:
        toast(f"Le dé {selected_die} ne peut pas aller au dépôt {depot_id}.")
        return

    # Spend workers if needed
    if workers_needed > 0:
        try:
            p.spend_workers(workers_needed)
        except Exception as e:
            toast(str(e))
            return

    # stockage
    if not p.can_store_hex_tile():
        toast("Stockage plein (max 3).")
        return

    # action côté game
    try:
        game.action_take_hex_from_depot(depot_id)
    except Exception as e:
        toast(str(e))
        return

    # consume die (player.py => remove from p.dice)
    try:
        p.use_die(selected_die)
    except Exception as e:
        toast(str(e))
        return

    toast(f"Tuile prise dépôt {depot_id} (dé {selected_die}, workers {workers_needed})")
    selected_die = None  # force re-sélection (plus clair)


def try_buy_black():
    """
    Achat dépôt noir :
    - dé sélectionné obligatoire (n'importe lequel)
    - coûte 2 silverlings (géré par game.action_take_hex_from_black_depot)
    - consomme le dé sélectionné
    """
    global selected_die

    p = current_player()

    if not ensure_rolled() or not ensure_selected_die():
        return

    try:
        game.action_take_hex_from_black_depot()
    except Exception as e:
        toast(str(e))
        return

    try:
        p.use_die(selected_die)
    except Exception as e:
        toast(str(e))
        return

    toast(f"Tuile noire achetée (dé {selected_die})")
    selected_die = None


# ===============================
# MAIN LOOP
# ===============================
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ===============================
        # MENU
        # ===============================
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
                    p.workers = 0
                    p.dice = []  # force roll
                set_active_player(0)

                mode = MODE_GAME
                current_view = VIEW_CENTRAL
                clear_dice_ui()
                reset_player_view_state()
                toast("Partie lancée")
            continue

        # ===============================
        # CLIC SOURIS
        # ===============================
        if mode == MODE_GAME and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            p = current_player()

            # ----------------------------
            # 1) CLICK SUR UN DÉ (HUD)
            # ----------------------------
            clicked_die = None
            for die_val, rect in DIE_RECTS.items():
                if rect.collidepoint(mx, my):
                    clicked_die = die_val
                    break

            if clicked_die is not None:
                if not ensure_rolled():
                    continue
                if clicked_die not in p.dice:
                    toast("Dé déjà utilisé.")
                else:
                    selected_die = clicked_die
                    toast(f"Dé sélectionné : {selected_die}", 1.2)
                continue

            # ----------------------------
            # 2) BOUTONS JOUEURS (switch vue)
            # ----------------------------
            if current_view == VIEW_CENTRAL:
                for i, rect in enumerate(PLAYER_BUTTONS):
                    if rect.collidepoint(mx, my):
                        set_active_player(i)
                        current_view = VIEW_PLAYER
                        reset_player_view_state()
                        break

            # ----------------------------
            # 3) HUD (ROLL / FIN)
            # ----------------------------
            if HUD_RECT.collidepoint(mx, my):
                if ROLL_BTN.collidepoint(mx, my):
                    # roll = Player.roll_dice()
                    p.roll_dice()
                    dice_a, dice_b = p.dice[0], p.dice[1]
                    selected_die = None
                    toast(f"Dés : {dice_a}, {dice_b}")
                elif ENDTURN_BTN.collidepoint(mx, my):
                    end_turn()
                continue

            # ----------------------------
            # 4) VUE CENTRALE : dépôts
            # ----------------------------
            if current_view == VIEW_CENTRAL:
                handled = False

                # click tuiles depots
                for (depot_id, idx), data in DEPOT_HEXES.items():
                    if data["rect"].collidepoint(mx, my):
                        # 1er clic = sélection visuelle
                        if selected_central_tile != (depot_id, idx):
                            selected_central_tile = (depot_id, idx)
                            toast(f"Tuile sélectionnée dépôt {depot_id}", 1.0)
                        else:
                            # 2e clic = tentative de prise avec dé sélectionné
                            try_take_from_depot(depot_id)
                            selected_central_tile = None
                        handled = True
                        break

                # depot noir
                if not handled and BLACK_DEPOT_RECT and BLACK_DEPOT_RECT.collidepoint(mx, my):
                    try_buy_black()
                    handled = True

            # ----------------------------
            # 5) VUE JOUEUR : retour
            # ----------------------------
            elif current_view == VIEW_PLAYER:
                if BACK_BUTTON.collidepoint(mx, my):
                    current_view = VIEW_CENTRAL
                    reset_player_view_state()

    # ===============================
    # RENDU
    # ===============================
    screen.fill(BACKGROUND_COLOR)
    mx, my = pygame.mouse.get_pos()

    if mode == MODE_MENU:
        screen.blit(
            FONT_BIG.render("Choisis un layout (1–9)", True, (255, 255, 255)),
            (WIDTH // 2 - 180, HEIGHT // 2 - 40),
        )

    elif mode == MODE_GAME:
        if toast_message and time.time() < toast_until:
            draw_toast(screen, TOAST_RECT, toast_message, FONT)

        if current_view == VIEW_CENTRAL:
            draw_central_board(screen, game.board, (80, 80), (mx, my), selected_central_tile)
            draw_steps(screen, game.players, (200, 80 + DEPOT_HEIGHT + 120))

            # Boutons joueurs
            for i, rect in enumerate(PLAYER_BUTTONS):
                pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=8)
                if i == current_player_index:
                    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
                txt = FONT.render(f"Joueur {i + 1}", True, (255, 255, 255))
                screen.blit(
                    txt,
                    (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2),
                )

        else:
            p = current_player()
            draw_player_board(screen, p.board, BOARD_ORIGIN, selected_hex, legal_coords)
            draw_storage(screen, p.hex_storage, selected_storage_index, (WIDTH // 2 - 90, HEIGHT - 120))

            pygame.draw.rect(screen, (60, 60, 60), BACK_BUTTON, border_radius=8)
            pygame.draw.rect(screen, (200, 200, 200), BACK_BUTTON, 2, border_radius=8)
            screen.blit(
                FONT.render("← Plateau central", True, (255, 255, 255)),
                (BACK_BUTTON.x + 12, BACK_BUTTON.y + 10),
            )

        # HUD (toujours visible)
        draw_panel(screen, HUD_RECT)

        # infos joueur
        p = current_player()
        screen.blit(FONT_SMALL.render(f"Actif: Joueur {current_player_index+1}", True, (230, 230, 230)),
                    (HUD_RECT.x + 12, HUD_RECT.y + 10))
        screen.blit(FONT_SMALL.render(f"Silver: {p.silverlings} | Workers: {p.workers}", True, (200, 200, 200)),
                    (HUD_RECT.x + 12, HUD_RECT.y + 32))
        screen.blit(FONT_SMALL.render(f"Dés restants: {len(p.dice)}", True, (200, 200, 200)),
                    (HUD_RECT.x + 12, HUD_RECT.y + 54))

        # Dés (cliquables) + highlight sélection
        DIE_RECTS.clear()
        if getattr(p, "dice", None):
            base_x = HUD_RECT.x + 75
            y = HUD_RECT.y + 105

            for i, die_val in enumerate(p.dice):
                x = base_x + i * 80
                draw_die(screen, (x, y), die_val, FONT)

                rect = pygame.Rect(x - 29, y - 29, 58, 58)
                DIE_RECTS[die_val] = rect

                # surbrillance si sélectionné
                if selected_die == die_val:
                    pygame.draw.rect(
                        screen,
                        (255, 255, 255),
                        rect,
                        3,
                        border_radius=10
                    )


        
        draw_button(screen, ROLL_BTN, "Roll", FONT_SMALL)
        draw_button(screen, ENDTURN_BTN, "Fin tour", FONT_SMALL)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
