# ui/render_central.py
import pygame
from render_hex import draw_hex
from board import TileType
from colors import TILE_COLORS, BORDER_COLOR

# ===============================
# CONSTANTES VISUELLES
# ===============================
DEPOT_WIDTH = 140
DEPOT_HEIGHT = 140
DEPOT_GAP = 18

HEX_SIZE = 20        # Taille des tuiles sur le plateau central
HEX_GAP = 12         # Espace entre les tuiles dans les dépôts

STEP_RADIUS = 22
STEP_GAP = 90
STEP_RECTS={}
# ===============================
# ZONES CLIQUABLES (Globales)
# ===============================
DEPOT_RECTS = {}
DEPOT_HEXES = {}
BLACK_DEPOT_RECT = None

def draw_central_board(screen, board, origin, mouse_pos=None, selected_tile=None):
    """
    Rendu du plateau central :
    - Dessine les 6 dépôts avec leurs tuiles (rognées en hexagone).
    - Gère le dépôt noir.
    - Met à jour les dictionnaires de collision pour les clics.
    """
    global DEPOT_RECTS, DEPOT_HEXES, BLACK_DEPOT_RECT

    DEPOT_RECTS.clear()
    DEPOT_HEXES.clear()

    ox, oy = origin
    font = pygame.font.SysFont(None, 24)

    # ===============================
    # DÉPÔTS 1 → 6
    # ===============================
    for depot_id in range(1, 7):
        # Calcul de la position du rectangle du dépôt
        x = ox + (depot_id - 1) * (DEPOT_WIDTH + DEPOT_GAP)
        y = oy

        depot_rect = pygame.Rect(x, y, DEPOT_WIDTH, DEPOT_HEIGHT)
        DEPOT_RECTS[depot_id] = depot_rect

        # Dessin du fond du dépôt
        pygame.draw.rect(screen, (50, 50, 50), depot_rect, border_radius=12)
        pygame.draw.rect(screen, (120, 120, 120), depot_rect, 2, border_radius=12)

        # Affichage du numéro du dé
        txt = font.render(str(depot_id), True, (255, 255, 255))
        screen.blit(txt, (x + 10, y + 8))

        # --- DESSIN DES TUILES (GRILLE 2x2) ---
        tiles = board.depots.get(depot_id, [])
        COLS = 2
        cell_step = HEX_SIZE * 2 + HEX_GAP

        # Centrage de la grille de tuiles dans le dépôt
        grid_w = COLS * cell_step - HEX_GAP
        start_x = x + (DEPOT_WIDTH - grid_w) // 2 + HEX_SIZE
        start_y = y + 48

        for i, tile in enumerate(tiles[:4]):  # Max 4 tuiles par dépôt
            col = i % COLS
            row = i // COLS

            hx = start_x + col * cell_step
            hy = start_y + row * cell_step

            # Rect pour la détection de survol/clic
            rect = pygame.Rect(hx - HEX_SIZE, hy - HEX_SIZE, HEX_SIZE * 2, HEX_SIZE * 2)
            
            is_hovered = mouse_pos and rect.collidepoint(mouse_pos)
            is_selected = selected_tile == (depot_id, i)

            # Couleur de fond (fallback si l'image .jpg est absente)
            base_color = TILE_COLORS.get(tile.tile_type, (150, 150, 150))
            if is_hovered:
                base_color = [min(c + 40, 255) for c in base_color]

            # APPEL AU RENDU HEXAGONAL (AVEC IMAGE)
            draw_hex(screen, (hx, hy), base_color, HEX_SIZE, tile=tile)

            # Feedback de sélection (cercle blanc)
            if is_selected:
                pygame.draw.circle(screen, (255, 255, 255), (hx, hy), HEX_SIZE + 4, 3)

            # Enregistrement pour le système de clic
            DEPOT_HEXES[(depot_id, i)] = {
                "rect": rect,
                "tile": tile,
            }

    # ===============================
    # DÉPÔT NOIR (8 tuiles avec dos noir: 2 colonnes x 4 rangées)
    # ===============================
    last_rect = DEPOT_RECTS[6]
    bx = last_rect.right + 25
    by = last_rect.top

    # Height for 4 rows of hex tiles
    black_depot_height = DEPOT_HEIGHT * 2
    BLACK_DEPOT_RECT = pygame.Rect(bx, by, DEPOT_WIDTH, black_depot_height)
    black_hover = mouse_pos and BLACK_DEPOT_RECT.collidepoint(mouse_pos)

    # Fond noir avec bordure dorée
    pygame.draw.rect(screen, (20, 20, 20), BLACK_DEPOT_RECT, border_radius=12)
    color_border = (255, 255, 255) if black_hover else (255, 215, 0)
    pygame.draw.rect(screen, color_border, BLACK_DEPOT_RECT, 2, border_radius=12)

    txt_noir = font.render("NOIR", True, (255, 215, 0))
    screen.blit(txt_noir, (bx + (DEPOT_WIDTH - txt_noir.get_width()) // 2, by + 10))

    # Dessin des 8 tuiles du dépôt noir
    black_tiles = board.black_depot
    for i, tile in enumerate(black_tiles[:8]):
        col, row = i % 2, i // 2
        hx = (bx + (DEPOT_WIDTH - grid_w) // 2 + HEX_SIZE) + col * cell_step
        hy = (by + 48) + row * cell_step

        draw_hex(screen, (hx, hy), TILE_COLORS.get(tile.tile_type), HEX_SIZE, tile=tile)

        # Enregistrement pour clic sur dépôt noir
        rect_n = pygame.Rect(hx - HEX_SIZE, hy - HEX_SIZE, HEX_SIZE * 2, HEX_SIZE * 2)
        DEPOT_HEXES[(0, i)] = {"rect": rect_n, "tile": tile}

def draw_steps(screen, players, origin):
    """Affiche la piste d'ordre de tour."""
    ox, oy = origin
    font_small = pygame.font.SysFont(None, 20)
    
    for step in range(1, 7):
        cx = ox + (step - 1) * STEP_GAP
        cy = oy

        # Cercle de base
        pygame.draw.circle(screen, (40, 40, 40), (cx, cy), STEP_RADIUS)
        pygame.draw.circle(screen, (180, 180, 180), (cx, cy), STEP_RADIUS, 2)

        txt = font_small.render(str(step), True, (255, 255, 255))
        screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

        # Jetons des joueurs
        players_here = [p for p in players if p.step_position == step]
        for i, p in enumerate(players_here):
            py = cy + STEP_RADIUS + 15 + i * 18
            pygame.draw.circle(screen, p.color, (cx, py), 8)
            if p.is_active:
                pygame.draw.circle(screen, (255, 255, 255), (cx, py), 10, 2)


def draw_bridge(screen, players, origin, current_player_index=0):
    """
    Affiche le pont (bridge) montrant l'ordre de jeu des joueurs.
    - Cases 1 à 4 : tous commencent sur 1, avancent vers 4
    - Plus la position est haute, plus le joueur joue tôt
    - Sur une même case, le joueur en HAUT de la pile joue en premier
    """
    ox, oy = origin
    font = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 18)
    
    # 4 cases : 1 (départ) à 4 (avancé)
    num_slots = 4
    
    # Dimensions du pont
    bridge_width = 320
    bridge_height = 100
    
    # Fond du pont (style bois)
    bridge_rect = pygame.Rect(ox, oy, bridge_width, bridge_height)
    pygame.draw.rect(screen, (101, 67, 33), bridge_rect, border_radius=8)
    pygame.draw.rect(screen, (139, 90, 43), bridge_rect, 3, border_radius=8)
    
    # Titre
    title = font.render("PONT - Ordre de jeu", True, (255, 255, 255))
    screen.blit(title, (ox + (bridge_width - title.get_width()) // 2, oy + 5))
    
    # Calcul des positions des cases
    slot_width = bridge_width // (num_slots + 1)
    base_y = oy + 55
    
    # Dessiner les 4 cases (1 à gauche = départ, 4 à droite = avancé)
    for slot in range(1, num_slots + 1):
        slot_x = ox + slot * slot_width
        
        # Cercle pour la case
        pygame.draw.circle(screen, (60, 40, 20), (slot_x, base_y), 18)
        # Couleur de bordure : plus verte si plus avancé
        green_factor = (slot - 1) / 3
        border_color = (
            int(255 * (1 - green_factor) + 100 * green_factor),
            int(200 * (1 - green_factor) + 255 * green_factor),
            int(100 * (1 - green_factor) + 100 * green_factor)
        )
        pygame.draw.circle(screen, border_color, (slot_x, base_y), 18, 2)
        
        # Numéro de case en dessous
        slot_txt = font_small.render(str(slot), True, (200, 180, 140))
        screen.blit(slot_txt, (slot_x - slot_txt.get_width() // 2, base_y + 22))
    
    # Indicateurs
    depart_txt = font_small.render("Départ", True, (255, 200, 100))
    screen.blit(depart_txt, (ox + slot_width - depart_txt.get_width() // 2, oy + bridge_height - 15))
    
    avance_txt = font_small.render("1er", True, (100, 255, 100))
    screen.blit(avance_txt, (ox + num_slots * slot_width - avance_txt.get_width() // 2, oy + bridge_height - 15))
    
    # Flèche montrant la direction d'avancement
    arrow_y = base_y
    pygame.draw.line(screen, (200, 200, 200), (ox + slot_width + 25, arrow_y), (ox + num_slots * slot_width - 25, arrow_y), 2)
    pygame.draw.polygon(screen, (200, 200, 200), [
        (ox + num_slots * slot_width - 25, arrow_y),
        (ox + num_slots * slot_width - 32, arrow_y - 5),
        (ox + num_slots * slot_width - 32, arrow_y + 5)
    ])
    
    # Grouper les joueurs par position
    positions_dict = {i: [] for i in range(1, num_slots + 1)}
    for i, p in enumerate(players):
        pos = max(1, min(num_slots, p.turn_order_position))  # Clamp entre 1 et 4
        positions_dict[pos].append((i, p))
    
    # Trier chaque groupe par bridge_stack_priority (plus haute = en haut)
    for pos in positions_dict:
        positions_dict[pos].sort(key=lambda x: x[1].bridge_stack_priority)
    
    # Dessiner les pions empilés sur chaque case
    for pos in range(1, num_slots + 1):
        player_list = positions_dict[pos]
        slot_x = ox + pos * slot_width
        
        # Empiler verticalement (celui avec priorité haute est en haut)
        for stack_idx, (player_idx, p) in enumerate(player_list):
            jeton_y = base_y - stack_idx * 10
            
            # Jeton du joueur (couleur)
            pygame.draw.circle(screen, p.color, (slot_x, jeton_y), 11)
            
            # Bordure
            if player_idx == current_player_index:
                pygame.draw.circle(screen, (255, 255, 255), (slot_x, jeton_y), 13, 3)
            else:
                pygame.draw.circle(screen, (30, 30, 30), (slot_x, jeton_y), 11, 2)
            
            # Numéro du joueur
            num_txt = font_small.render(str(player_idx + 1), True, (255, 255, 255))
            screen.blit(num_txt, (slot_x - num_txt.get_width() // 2, 
                                  jeton_y - num_txt.get_height() // 2))