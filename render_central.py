# ui/render_central.py
import pygame
from render_hex import draw_hex
from board import TileType
from colors import TILE_COLORS, BORDER_COLOR, GOODS_COLORS

# ===============================
# CONSTANTES VISUELLES
# ===============================
DEPOT_WIDTH = 140
DEPOT_HEIGHT = 140
DEPOT_GAP = 18

GOODS_BOX_HEIGHT = 50  # Hauteur des boîtes de marchandises
GOODS_BOX_GAP = 8      # Espace entre dépôt tuiles et dépôt marchandises

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
GOODS_RECTS = {}     # Rectangles cliquables pour les marchandises
BLACK_DEPOT_RECT = None

def draw_central_board(screen, board, origin, mouse_pos=None, selected_tile=None):
    """
    Rendu du plateau central :
    - Dessine les 6 dépôts avec leurs tuiles (rognées en hexagone).
    - Gère le dépôt noir.
    - Met à jour les dictionnaires de collision pour les clics.
    """
    global DEPOT_RECTS, DEPOT_HEXES, GOODS_RECTS, BLACK_DEPOT_RECT

    DEPOT_RECTS.clear()
    DEPOT_HEXES.clear()
    GOODS_RECTS.clear()

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
    # BOÎTES DE MARCHANDISES (séparées, sous les dépôts de tuiles)
    # ===============================
    for depot_id in range(1, 7):
        x = ox + (depot_id - 1) * (DEPOT_WIDTH + DEPOT_GAP)
        goods_y = oy + DEPOT_HEIGHT + GOODS_BOX_GAP
        
        goods_rect = pygame.Rect(x, goods_y, DEPOT_WIDTH, GOODS_BOX_HEIGHT)
        GOODS_RECTS[depot_id] = goods_rect
        
        # Fond de la boîte de marchandises
        pygame.draw.rect(screen, (40, 35, 30), goods_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 90, 80), goods_rect, 2, border_radius=8)
        
        # Dessiner les marchandises dans cette boîte
        goods = board.depot_goods.get(depot_id, [])
        goods_size = 18
        goods_gap = 6
        total_goods_width = len(goods) * goods_size + (len(goods) - 1) * goods_gap if goods else 0
        goods_start_x = x + (DEPOT_WIDTH - total_goods_width) // 2
        
        for gi, g in enumerate(goods[:6]):  # Max 6 marchandises affichées
            gx = goods_start_x + gi * (goods_size + goods_gap)
            gy = goods_y + (GOODS_BOX_HEIGHT - goods_size) // 2
            goods_color = GOODS_COLORS.get(g.color, (150, 150, 150))
            pygame.draw.rect(screen, goods_color, (gx, gy, goods_size, goods_size), border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), (gx, gy, goods_size, goods_size), 1, border_radius=3)
        
        # Si pas de marchandises, afficher un placeholder
        if not goods:
            empty_txt = pygame.font.SysFont(None, 16).render("(vide)", True, (80, 80, 80))
            screen.blit(empty_txt, (x + (DEPOT_WIDTH - empty_txt.get_width()) // 2, goods_y + (GOODS_BOX_HEIGHT - empty_txt.get_height()) // 2))

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