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

FONT_DEBUG = pygame.font.SysFont(None, 18)
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
MODE_GAME_OVER = "game_over"
VIEW_CENTRAL = "central"
VIEW_PLAYER = "player"

mode = MODE_MENU
current_view = VIEW_CENTRAL
viewed_player_index = 0  # plateau affiché (peut être différent du joueur actif)

# ===============================
# ÉTAT GLOBAL
# ===============================
selected_layout_id = 1
selected_central_tile = None
game = None

selected_storage_index = None
legal_coords = set()
BOARD_ORIGIN = (WIDTH // 2, HEIGHT // 2)

# ===============================
# UI
# ===============================
PLAYER_BUTTONS = [pygame.Rect(50 + i * 120, HEIGHT - 70, 100, 40) for i in range(4)]
BACK_BUTTON = pygame.Rect(20, 20, 180, 40)

HUD_RECT = pygame.Rect(WIDTH - 320, HEIGHT - 260, 300, 240)
ROLL_BTN = pygame.Rect(HUD_RECT.x + 20, HUD_RECT.y + 190, 120, 35)
ENDTURN_BTN = pygame.Rect(HUD_RECT.x + 160, HUD_RECT.y + 190, 120, 35)
WORKER_ACTION_BTN = pygame.Rect(HUD_RECT.x + 20, HUD_RECT.y + 90, 120, 30)
SELL_ACTION_BTN = pygame.Rect(HUD_RECT.x + 160, HUD_RECT.y + 90, 120, 30)

TOAST_RECT = pygame.Rect(20, 20, 520, 46)
toast_message = ""
toast_until = 0.0

selected_die_idx = None          # index dans p.dice
DIE_RECTS = {}                   # idx -> rect

# ===============================
# HELPERS
# ===============================
def toast(msg, seconds=2.5):
    global toast_message, toast_until
    toast_message = msg
    toast_until = time.time() + seconds
    print("[UI]", msg)


def replenish_black_depot():
    """Replenish the 8 spaces of the black depot with random hex tiles with black backs."""
    board = game.board
    board.black_depot.clear()
    for _ in range(8):
        if board._black_supply:
            board.black_depot.append(board._black_supply.pop())
        else:
            break
    print(f"[UI] Black depot replenished with {len(board.black_depot)} tiles")


def reset_player_view_state():
    global selected_storage_index, selected_central_tile, legal_coords
    selected_storage_index = None
    selected_central_tile = None
    legal_coords = set()

def turn_player():
    return game.players[game.current_player_index]

def viewed_player():
    return game.players[viewed_player_index]

def clear_dice_ui():
    global selected_die_idx
    selected_die_idx = None
    DIE_RECTS.clear()

def get_selected_die(player):
    global selected_die_idx
    if selected_die_idx is None:
        return None
    if not getattr(player, "dice", None):
        selected_die_idx = None
        return None
    if selected_die_idx < 0 or selected_die_idx >= len(player.dice):
        selected_die_idx = None
        return None
    return player.dice[selected_die_idx]

def end_turn():
    global viewed_player_index, mode
    
    # Sauvegarder le round actuel avant next_player pour détecter le changement de phase
    old_round = game.global_round
    
    game.next_player()
    
    # Vérifier si la partie est terminée (fin de Phase E = round 25)
    # Phase E = rounds 21-25, donc après round 25, global_round devient 26
    if game.global_round > 25:
        mode = MODE_GAME_OVER
        toast("Partie terminée !")
        return
    
    # Vérifier si on commence une nouvelle phase (round 6, 11, 16, 21)
    # Chaque phase dure 5 rounds: A=1-5, B=6-10, C=11-15, D=16-20, E=21-25
    new_round = game.global_round
    if new_round != old_round and new_round in (6, 11, 16, 21):
        replenish_black_depot()
        phase_letter = chr(65 + ((new_round - 1) // 5))
        toast(f"Nouvelle phase {phase_letter} ! Dépôt noir réapprovisionné.")
    
    p = turn_player()
    p.dice = []  # force reroll
    clear_dice_ui()
    reset_player_view_state()
    viewed_player_index = game.current_player_index
    toast(f"Au tour de {p.name}")

def calculate_worker_cost(die_val, target_val):
    if die_val == target_val:
        return 0
    diff = abs(die_val - target_val)
    return min(diff, 6 - diff)

def try_take_from_depot(depot_id: int, tile_index: int):
    """Prend EXACTEMENT la tuile cliquée dans le dépôt (pas aléatoire)."""
    p = turn_player()
    die_val = get_selected_die(p)
    if die_val is None:
        toast("Sélectionne un dé d'abord !")
        return

    workers_needed = calculate_worker_cost(die_val, depot_id)
    if p.workers < workers_needed:
        toast(f"Besoin de {workers_needed} ouvriers")
        return

    if not p.can_store_hex_tile():
        toast("Stockage plein !")
        return

    depot = game.board.depots.get(depot_id, [])
    if tile_index < 0 or tile_index >= len(depot):
        toast("Tuile invalide")
        return

    try:
        tile = depot.pop(tile_index)            # <-- exact tile
        if workers_needed > 0:
            p.workers -= workers_needed

        p.add_hex_to_storage(tile)
        p.use_die(die_val)

        clear_dice_ui()
        toast(f"Tuile prise (dépôt {depot_id})")
    except Exception as e:
        toast(str(e))

def try_buy_black(tile_index: int = 0):
    """
    Achat dépôt noir. Coûte 2 silverlings, NE consomme PAS de dé.
    Peut être fait à n'importe quel moment du tour, en plus des 2 actions de dé.
    """
    p = turn_player()

    if p.silverlings < 2:
        toast("Pas assez d'argent (2 silverlings requis) !")
        return

    if not p.can_store_hex_tile():
        toast("Stockage plein !")
        return

    black = game.board.black_depot
    if not black:
        toast("Dépôt noir vide")
        return
    if tile_index < 0 or tile_index >= len(black):
        tile_index = 0

    try:
        tile = black.pop(tile_index)
        p.silverlings -= 2
        p.add_hex_to_storage(tile)
        # PAS de p.use_die() - l'achat du dépôt noir ne consomme pas de dé
        toast("Tuile noire achetée (2 silverlings)")
    except Exception as e:
        toast(str(e))

def try_take_workers_action():
    p = turn_player()
    die_val = get_selected_die(p)
    if die_val is None:
        toast("Sélectionne un dé")
        return

    try:
        p.workers += 2
        p.use_die(die_val)
        clear_dice_ui()
        toast("+2 Ouvriers")
    except Exception as e:
        toast(str(e))

def compute_legal_coords_for_storage_tile(player, storage_index):
    """Cases où la tuile du storage_index peut être placée (type OK + slots vides)."""
    coords = set()
    if storage_index is None:
        return coords
    if storage_index < 0 or storage_index >= len(player.hex_storage):
        return coords
    tile = player.hex_storage[storage_index]
    if tile is None:
        return coords

    tile_type = tile.tile_type

    # get_valid_placement_coords() renvoie déjà des coords "posables" selon règles de ton Player
    # on filtre en plus sur type de région
    try:
        for coord, die_val, wk in player.get_valid_placement_coords():
            slot = player.board.hex_map.get_slot(coord)
            if slot and (not slot.is_occupied) and slot.allowed_type == tile_type:
                coords.add(coord)
    except Exception:
        # fallback: au minimum, slots vides de même type
        for coord, slot in player.board.hex_map.grid.items():
            if (not slot.is_occupied) and slot.allowed_type == tile_type:
                coords.add(coord)

    return coords

def can_place_with_selected_die(player, coord, die_val):
    """
    Valide le placement AVEC le dé sélectionné.
    Retourne (ok, workers_needed).
    """
    slot = player.board.hex_map.get_slot(coord)
    if slot is None:
        return False, 0

    target_value = slot.dice_value
    tile_type = slot.allowed_type

    if die_val == target_value:
        return True, 0

    if player.get_free_placement_die_adjustment(tile_type):
        return True, 0

    try:
        return player.can_reach_value_with_workers(target_value, die_val)
    except Exception:
        return False, 0

def try_place_tile_on_board(clicked_coord):
    """
    Flow demandé :
    1) cliquer dé
    2) cliquer tuile stockage
    3) cliquer case
    => si ok : place + consomme dé + workers nécessaires
    """
    global selected_storage_index, legal_coords

    p_turn = turn_player()
    p_view = viewed_player()

    if viewed_player_index != game.current_player_index:
        toast("Ce n'est pas ton tour")
        return

    if selected_storage_index is None:
        toast("Clique d'abord sur une tuile du stockage")
        return

    die_val = get_selected_die(p_turn)
    if die_val is None:
        toast("Sélectionne un dé valide")
        return

    if clicked_coord not in legal_coords:
        toast("Case non valide")
        return

    ok, wk_needed = can_place_with_selected_die(p_view, clicked_coord, die_val)
    
    if not ok:
        toast("Placement illégal")
        return
    if p_view.workers < wk_needed:
        toast(f"Besoin de {wk_needed} ouvriers")
        return

    tile_to_place = None
    if 0 <= selected_storage_index < len(p_view.hex_storage):
        tile_to_place = p_view.hex_storage[selected_storage_index]
    if tile_to_place is None:
        toast("Tuile invalide")
        return

    slot = p_view.board.hex_map.get_slot(clicked_coord)
    if slot is None:
        toast("Case non valide")
        return

    effective_die_value = slot.dice_value if (wk_needed > 0 or p_view.get_free_placement_die_adjustment(slot.allowed_type)) else die_val
    if not p_view.board.can_place_tile_at(tile_to_place, clicked_coord, p_view, effective_die_value):
        toast("Placement illégal")
        return

    try:
        game.action_place_tile_from_storage(
            selected_storage_index,
            clicked_coord,
            game.global_round,
            die_val,
            wk_needed
        )
        toast("Tuile placée ✔")
        reset_player_view_state()
        clear_dice_ui()
    except Exception as e:
        toast(str(e))

# ===============================
# MAIN LOOP
# ===============================
running = True
while running:
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---------------------------
        # MENU
        # ---------------------------
        if mode == MODE_MENU and event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                selected_layout_id = event.key - pygame.K_0
                toast(f"Layout {selected_layout_id}", 1.0)

            if event.key == pygame.K_RETURN:
                game = Game(["Alice", "Bob", "Clément", "Diane"])
                for i, p in enumerate(game.players):
                    # init board/layout
                    p.layout_id = selected_layout_id
                    p.__post_init__()  # ta logique existante

                    # ✅ évite l'erreur render_central.py: p.color
                    p.color = PLAYER_COLORS[i]
                    p.is_active = (i == 0)

                    # init ressources
                    p.silverlings = 2
                    p.workers = 1 + i
                    p.dice = []

                    # si ton code dépend de step_position
                    if not hasattr(p, "step_position"):
                        p.step_position = 1

                mode = MODE_GAME
                current_view = VIEW_CENTRAL
                viewed_player_index = game.current_player_index
                clear_dice_ui()  # reset
                reset_player_view_state()
                toast("Partie lancée")
            continue

        # ---------------------------
        # JEU - CLIC
        # ---------------------------
        if mode == MODE_GAME and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            p_turn = turn_player()

            # sécurité : si dé sélectionné out-of-range
            if selected_die_idx is not None and (not p_turn.dice or selected_die_idx >= len(p_turn.dice)):
                clear_dice_ui()

            # (A) BACK BUTTON en vue joueur (PRIORITÉ)
            if current_view == VIEW_PLAYER and BACK_BUTTON.collidepoint(mx, my):
                current_view = VIEW_CENTRAL
                reset_player_view_state()
                continue

            # (B) clic sur dés (HUD) => sélection
            clicked_die = False
            for idx, rect in DIE_RECTS.items():
                if rect.collidepoint(mx, my):
                    if idx < len(p_turn.dice):
                        selected_die_idx = idx
                        toast(f"Dé {p_turn.dice[idx]} sélectionné", 1.0)
                    else:
                        clear_dice_ui()
                    clicked_die = True
                    break
            if clicked_die:
                continue

            # (C) HUD boutons
            if HUD_RECT.collidepoint(mx, my):
                if ROLL_BTN.collidepoint(mx, my):
                    # ✅ pas de roll en vue player (comme tu veux)
                    if current_view != VIEW_CENTRAL:
                        toast("Roll uniquement sur le plateau central")
                    else:
                        p_turn.roll_dice()
                        clear_dice_ui()
                        reset_player_view_state()
                        toast(f"Dés: {p_turn.dice}", 1.5)
                elif ENDTURN_BTN.collidepoint(mx, my):
                    end_turn()
                elif WORKER_ACTION_BTN.collidepoint(mx, my):
                    try_take_workers_action()
                # SELL_ACTION_BTN: à implémenter si tu veux
                continue

            # (D) vue centrale : switch vers un player board
            if current_view == VIEW_CENTRAL:
                for i, rect in enumerate(PLAYER_BUTTONS):
                    if rect.collidepoint(mx, my):
                        viewed_player_index = i
                        current_view = VIEW_PLAYER
                        reset_player_view_state()
                        break

                # clic tuile dépôt (exacte)
                handled = False
                for (depot_id, idx), data in DEPOT_HEXES.items():
                    if data["rect"].collidepoint(mx, my):
                        if depot_id == 0:
                            try_buy_black(idx)
                        else:
                            try_take_from_depot(depot_id, idx)
                        handled = True
                        break

                # clic dépôt noir (zone)
                if not handled and BLACK_DEPOT_RECT and BLACK_DEPOT_RECT.collidepoint(mx, my):
                    try_buy_black(0)
                continue

            # (E) vue player : sélection storage ou placement
            if current_view == VIEW_PLAYER:
                # sécurité : uniquement joueur actif peut agir
                if viewed_player_index != game.current_player_index:
                    toast(f"C'est le tour de {p_turn.name}, pas de {viewed_player().name} !")
                    continue

                p_view = viewed_player()

                # 1) clic sur storage => sélection tuile + calc legal coords
                storage_origin = (WIDTH // 2 - 90, HEIGHT - 120)
                clicked_storage = False
                for i in range(3):
                    slot_rect = pygame.Rect(storage_origin[0] + i * 70, storage_origin[1], 50, 50)
                    if slot_rect.collidepoint(mx, my):
                        if i < len(p_view.hex_storage) and p_view.hex_storage[i] is not None:
                            selected_storage_index = i
                            legal_coords = compute_legal_coords_for_storage_tile(p_view, i)
                            toast("Tuile du stockage sélectionnée", 1.0)
                        else:
                            selected_storage_index = None
                            legal_coords = set()
                            toast("Slot vide", 1.0)
                        clicked_storage = True
                        break
                if clicked_storage:
                    continue

                # 2) clic sur une case => tentative placement (si dé + storage déjà choisis)
                clicked_coord = pixel_to_axial(mx, my, BOARD_ORIGIN)
                try_place_tile_on_board(clicked_coord)
                continue

    # ===============================
    # RENDU
    # ===============================
    screen.fill(BACKGROUND_COLOR)

    if mode == MODE_MENU:
        screen.blit(
            FONT_BIG.render("Choisis un layout (1–9) puis ENTER", True, (255, 255, 255)),
            (WIDTH // 2 - 260, HEIGHT // 2 - 40),
        )
        pygame.display.flip()
        clock.tick(60)
        continue

    if mode == MODE_GAME_OVER:
        # Afficher l'écran de fin de partie
        screen.blit(
            FONT_BIG.render("PARTIE TERMINÉE !", True, (255, 215, 0)),
            (WIDTH // 2 - 150, HEIGHT // 2 - 100),
        )
        # Afficher les scores
        sorted_players = sorted(game.players, key=lambda p: p.victory_points, reverse=True)
        for i, p in enumerate(sorted_players):
            color = (255, 255, 0) if i == 0 else (255, 255, 255)
            screen.blit(
                FONT.render(f"{i+1}. {p.name}: {p.victory_points} points", True, color),
                (WIDTH // 2 - 120, HEIGHT // 2 - 30 + i * 40),
            )
        pygame.display.flip()
        clock.tick(60)
        continue

    # MODE_GAME
    phase = chr(65 + ((game.global_round - 1) // 5))
    tour = ((game.global_round - 1) % 5) + 1
    screen.blit(FONT.render(f"PHASE {phase} - TOUR {tour}/5", True, (255, 255, 255)), (WIDTH // 2 - 110, 20))

    if current_view == VIEW_CENTRAL:
        draw_central_board(screen, game.board, (80, 80), (mx, my), selected_central_tile)
        draw_steps(screen, game.players, (200, 450))

        for i, rect in enumerate(PLAYER_BUTTONS):
            draw_button(screen, rect, f"Joueur {i+1}", FONT_SMALL, active=(i == viewed_player_index))
    else:
        p_v = viewed_player()

        # ton draw_player_board modifié (avec FONT_DEBUG en param)
        # signature attendue chez toi: draw_player_board(surface, player_board, origin, font_debug, selected_hex, legal_coords)
        hovered = pixel_to_axial(mx, my, BOARD_ORIGIN)
        try:
            draw_player_board(screen, p_v.board, BOARD_ORIGIN, FONT_DEBUG, hovered, legal_coords)
        except TypeError:
            # fallback si signature différente
            draw_player_board(screen, p_v.board, BOARD_ORIGIN, hovered, legal_coords)

        draw_storage(screen, p_v.hex_storage, selected_storage_index, (WIDTH // 2 - 90, HEIGHT - 120))
        draw_button(screen, BACK_BUTTON, "← Central", FONT_SMALL)

    # HUD (toujours visible)
    draw_panel(screen, HUD_RECT)
    p_t = turn_player()
    screen.blit(FONT_SMALL.render(f"TOUR DE : {p_t.name}", True, (255, 255, 0)), (HUD_RECT.x + 20, HUD_RECT.y + 15))
    screen.blit(
        FONT_SMALL.render(f"Arg:{p_t.silverlings} | Ouv:{p_t.workers} | Pts:{p_t.victory_points}", True, (255, 255, 255)),
        (HUD_RECT.x + 20, HUD_RECT.y + 45),
    )

    draw_button(screen, WORKER_ACTION_BTN, "+2 Ouvriers", FONT_SMALL)
    draw_button(screen, SELL_ACTION_BTN, "Vendre", FONT_SMALL)

    # Dés cliquables + highlight par INDEX (plus de bug si deux dés ont même valeur)
    DIE_RECTS.clear()
    for i, val in enumerate(getattr(p_t, "dice", [])):
        dx, dy = HUD_RECT.x + 60 + i * 80, HUD_RECT.y + 140
        draw_die(screen, (dx, dy), val, FONT)
        rect = pygame.Rect(dx - 27, dy - 27, 54, 54)
        DIE_RECTS[i] = rect
        if selected_die_idx == i:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3, border_radius=10)

    draw_button(screen, ROLL_BTN, "Roll", FONT_SMALL)
    draw_button(screen, ENDTURN_BTN, "Fin Tour", FONT_SMALL)

    if toast_message and time.time() < toast_until:
        draw_toast(screen, TOAST_RECT, toast_message, FONT)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
