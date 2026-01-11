# ui/main.py
import pygame
import time

from Game1 import Game
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
# ETAT GLOBAL
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
PLAYER_BUTTONS = [pygame.Rect(50 + i * 120, HEIGHT - 80, 100, 40) for i in range(4)]
BACK_BUTTON = pygame.Rect(20, 20, 170, 40)

HUD_RECT = pygame.Rect(WIDTH - 310, 20, 290, 230)
ROLL_BTN = pygame.Rect(WIDTH - 290, 170, 120, 40)
ENDTURN_BTN = pygame.Rect(WIDTH - 160, 170, 120, 40)

TOAST_RECT = pygame.Rect(20, 20, 520, 46)
toast_message = ""
toast_until = 0.0

# Dés affichés (valeurs)
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
    for p in game.players:
        p.is_active = False
    game.players[index].is_active = True


def get_silverlings(p):
    return getattr(p, "silverlings", 0)


def spend_silverlings(p, amount):
    if get_silverlings(p) < amount:
        return False
    p.silverlings -= amount
    return True


def has_rolled_backend() -> bool:
    return bool(getattr(game, "turn_started", False))


def actions_left_backend() -> int:
    # 2 actions = 2 dés max
    p = game.players[current_player_index]
    used = getattr(p, "used_dice", [])
    return max(0, 2 - len(used))


def require_roll_and_actions():
    if not has_rolled_backend():
        toast("Lance d'abord les dés (Roll / R)")
        return False
    if actions_left_backend() <= 0:
        toast("Plus d'actions disponibles (Fin tour)")
        return False
    return True


def consume_one_action_auto_die() -> bool:
    """
    Consomme automatiquement 1 dé non utilisé.
    (En attendant qu'on implémente la sélection de dé.)
    """
    p = game.players[current_player_index]
    dice = getattr(p, "dice", [])
    used = getattr(p, "used_dice", [])
    for d in dice:
        if d not in used:
            try:
                game.use_die(d)
                toast(f"Action utilisée (dé {d}) | reste {actions_left_backend()}", 1.2)
                return True
            except Exception as e:
                toast(str(e))
                return False

    toast("Aucun dé disponible", 1.2)
    return False


def end_turn():
    global selected_central_tile, current_view, dice_a, dice_b, white_die

    # fin de tour backend
    try:
        game.end_turn()
    except Exception:
        pass

    # sync UI index (simple)
    set_active_player((current_player_index + 1) % len(game.players))

    # reset UI + sélection
    selected_central_tile = None
    reset_player_view_state()
    current_view = VIEW_CENTRAL

    # reset affichage dés (optionnel)
    dice_a, dice_b = 1, 1

    toast(f"Tour -> Joueur {current_player_index + 1}")


# ===============================
# MAIN LOOP
# ===============================
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # MENU
        if mode == MODE_MENU and event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                selected_layout_id = event.key - pygame.K_0
                toast(f"Layout {selected_layout_id}", 1.2)

            if event.key == pygame.K_RETURN:
                game = Game(["Player 1", "Player 2", "Player 3", "Player 4"])
                for i, p in enumerate(game.players):
                    p.board = PlayerBoard(layout_id=selected_layout_id)
                    p.add_hex_to_storage(Tile(TileType.BUILDING))
                    p.color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                    p.step_position = 1
                    p.is_active = False
                    p.silverlings = 5
                    p.used_dice = []
                    p.dice = [1, 1]

                set_active_player(0)
                reset_player_view_state()
                selected_central_tile = None
                current_view = VIEW_CENTRAL
                mode = MODE_GAME
                toast("Partie lancée")
            continue

        # CLAVIER JEU
        if mode == MODE_GAME and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_view = VIEW_CENTRAL
                reset_player_view_state()
                selected_central_tile = None

            # Roll (R) -> backend
            if event.key == pygame.K_r and current_view == VIEW_CENTRAL:
                try:
                    res = game.start_turn()
                    dice_a, dice_b = res["dice"]
                    white_die = res["white_die"]
                    toast(f"Dés: {dice_a}, {dice_b} | blanc {white_die}")
                except Exception as e:
                    toast(str(e))

            # Fin tour (SPACE)
            if event.key == pygame.K_SPACE:
                end_turn()

        # SOURIS JEU
        if mode == MODE_GAME and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            active = game.players[current_player_index]

            if current_view == VIEW_CENTRAL:
                handled = False

                # A) HUD buttons
                if HUD_RECT.collidepoint(mx, my):
                    if ROLL_BTN.collidepoint(mx, my):
                        try:
                            res = game.start_turn()
                            dice_a, dice_b = res["dice"]
                            white_die = res["white_die"]
                            toast(f"Dés: {dice_a}, {dice_b} | blanc {white_die}")
                        except Exception as e:
                            toast(str(e))
                        handled = True

                    elif ENDTURN_BTN.collidepoint(mx, my):
                        end_turn()
                        handled = True

                # B) Clic tuile centrale (sélection + double clic => prendre)
                if not handled:
                    for (depot_id, idx), data in list(DEPOT_HEXES.items()):
                        if data["rect"].collidepoint(mx, my):

                            # 1er clic = select
                            if selected_central_tile != (depot_id, idx):
                                selected_central_tile = (depot_id, idx)
                                toast(f"Tuile sélectionnée (dépôt {depot_id})", 1.0)
                                handled = True
                                break

                            # 2e clic = prendre (action)
                            if not require_roll_and_actions():
                                handled = True
                                break

                            try:
                                tile = game.board.depots[depot_id].pop(idx)
                                active.add_hex_to_storage(tile)
                                toast("Tuile prise", 1.2)
                                consume_one_action_auto_die()
                            except Exception as e:
                                toast(str(e))

                            selected_central_tile = None
                            handled = True
                            break

                # C) Dépôt noir (achat 2) = action
                if not handled and BLACK_DEPOT_RECT and BLACK_DEPOT_RECT.collidepoint(mx, my):
                    if not require_roll_and_actions():
                        handled = True
                    else:
                        if spend_silverlings(active, 2):
                            try:
                                tile = game.board.take_hex_from_black_depot()
                                active.add_hex_to_storage(tile)
                                toast("Tuile noire achetée (-2)", 1.2)
                                consume_one_action_auto_die()
                            except Exception as e:
                                toast(str(e))
                        else:
                            toast("Pas assez d'argent (2)", 1.2)
                        selected_central_tile = None
                        handled = True

                # D) Marches (si tu veux que ça coûte une action, laisse comme ça)
                if not handled:
                    for step, rect in STEP_RECTS.items():
                        if rect.collidepoint(mx, my):
                            if not require_roll_and_actions():
                                handled = True
                                break
                            active.step_position = step
                            toast(f"{active.name} -> marche {step}", 1.2)
                            consume_one_action_auto_die()
                            handled = True
                            break

                # E) Boutons joueurs (pas une action)
                if not handled:
                    for i, rect in enumerate(PLAYER_BUTTONS):
                        if rect.collidepoint(mx, my):
                            set_active_player(i)
                            current_view = VIEW_PLAYER
                            reset_player_view_state()
                            selected_central_tile = None
                            break

            elif current_view == VIEW_PLAYER:
                mx, my = pygame.mouse.get_pos()

                if BACK_BUTTON.collidepoint(mx, my):
                    current_view = VIEW_CENTRAL
                    reset_player_view_state()
                    selected_central_tile = None
                    continue

                player = game.players[current_player_index]
                coord = pixel_to_axial(mx, my, BOARD_ORIGIN)

                if coord in player.board.hex_map.grid:
                    selected_hex = coord

                # pose tuile = action
                if selected_tile and selected_storage_index is not None and coord in legal_coords:
                    if not require_roll_and_actions():
                        reset_player_view_state()
                    else:
                        try:
                            # ⚠️ Ton Game1 actuel attend (storage_index, coord, die_value)
                            # mais ton UI passe (round, ctx). Donc on appelle directement le board:
                            tile = player.remove_hex_from_storage(selected_storage_index)
                            player.board.place_tile(tile, coord, current_round=getattr(game, "round", 1), player=player)
                            toast("Tuile posée", 1.2)
                            consume_one_action_auto_die()
                        except Exception as e:
                            toast(str(e))
                        reset_player_view_state()

                # clic stockage (pas une action)
                sx, sy = WIDTH // 2 - 90, HEIGHT - 120
                for i in range(3):
                    rect = pygame.Rect(sx + i * 70, sy, 50, 50)
                    if rect.collidepoint(mx, my) and i < len(player.hex_storage):
                        selected_storage_index = i
                        selected_tile = player.hex_storage[i]

    # LOGIQUE GUI
    if mode == MODE_GAME and current_view == VIEW_PLAYER and selected_tile:
        player = game.players[current_player_index]
        legal_coords.clear()
        for c in player.board.hex_map.grid:
            if player.board.can_place_tile_at(selected_tile, c, player):
                legal_coords.add(c)

    # RENDU
    screen.fill(BACKGROUND_COLOR)
    mx, my = pygame.mouse.get_pos()

    if mode == MODE_MENU:
        screen.blit(FONT_BIG.render("Choisis un layout (1–9)", True, (255, 255, 255)),
                    (WIDTH // 2 - 180, HEIGHT // 2 - 50))

    elif mode == MODE_GAME:
        if toast_message and time.time() < toast_until:
            draw_toast(screen, TOAST_RECT, toast_message, FONT)

        if current_view == VIEW_CENTRAL:
            draw_central_board(screen, game.board, (100, 100), (mx, my), selected_central_tile)
            draw_steps(screen, game.players, (150, 100 + DEPOT_HEIGHT + 140))

            # boutons joueurs
            for i, rect in enumerate(PLAYER_BUTTONS):
                pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=10)
                if i == current_player_index:
                    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=10)
                txt = FONT.render(f"Joueur {i + 1}", True, (255, 255, 255))
                screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

            # HUD
            draw_panel(screen, HUD_RECT)

            p = game.players[current_player_index]
            screen.blit(FONT_SMALL.render(f"Joueur actif: {current_player_index + 1}", True, (230, 230, 230)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 12))
            screen.blit(FONT_SMALL.render(f"Argent: {get_silverlings(p)}", True, (200, 200, 200)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 34))

            actions_left = actions_left_backend()
            rolled = has_rolled_backend()
            screen.blit(FONT_SMALL.render(f"Actions: {actions_left} | Roll: {'oui' if rolled else 'non'}", True, (200, 200, 200)),
                        (HUD_RECT.x + 14, HUD_RECT.y + 56))

            draw_die(screen, (HUD_RECT.x + 60, HUD_RECT.y + 110), dice_a, FONT)
            draw_die(screen, (HUD_RECT.x + 130, HUD_RECT.y + 110), dice_b, FONT)
            draw_die(screen, (HUD_RECT.x + 220, HUD_RECT.y + 110), white_die, FONT_SMALL, size=44)

            draw_button(screen, ROLL_BTN, "Roll (R)", FONT_SMALL)
            draw_button(screen, ENDTURN_BTN, "Fin tour", FONT_SMALL)

        else:
            player = game.players[current_player_index]
            draw_player_board(screen, player.board, BOARD_ORIGIN, selected_hex, legal_coords)
            draw_storage(screen, player.hex_storage, selected_storage_index, (WIDTH // 2 - 90, HEIGHT - 120))

            pygame.draw.rect(screen, (60, 60, 60), BACK_BUTTON, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), BACK_BUTTON, 2, border_radius=10)
            screen.blit(FONT.render("← Plateau central", True, (255, 255, 255)),
                        (BACK_BUTTON.x + 12, BACK_BUTTON.y + 10))

            # mini HUD
            actions_left = actions_left_backend()
            rolled = has_rolled_backend()
            screen.blit(FONT_SMALL.render(f"Actions: {actions_left} | Roll: {'oui' if rolled else 'non'}", True, (230, 230, 230)),
                        (20, 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
