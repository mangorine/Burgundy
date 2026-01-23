import pygame
import os
from render_hex import draw_hex
from board import TileType, GoodsColor

# ===============================
# CONSTANTES VISUELLES
# ===============================
DEPOT_WIDTH = 110
DEPOT_HEIGHT = 120
DEPOT_GAP = 20
STEP_RADIUS = 22
STEP_GAP = 20
STEP_RECTS = {}   # { (player_index, step): Rect }

HEX_SIZE = 14
GOODS_SIZE = 24  # Size of goods images

TILE_COLORS = {
    TileType.CASTLE: (200, 200, 200),
    TileType.BUILDING: (200, 150, 80),
    TileType.SHIP: (80, 140, 220),
    TileType.MINE: (120, 120, 120),
    TileType.ANIMAL: (120, 200, 120),
    TileType.KNOWLEDGE: (170, 120, 200),
}

# ===============================
# CHARGEMENT DES IMAGES DE MARCHANDISES
# ===============================
GOODS_IMAGES = {}

def load_goods_images():
    """Load goods images from the images/goods folder."""
    global GOODS_IMAGES
    if GOODS_IMAGES:  # Already loaded
        return
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    goods_path = os.path.join(base_path, "images", "goods")
    
    for i in range(1, 7):
        img_file = os.path.join(goods_path, f"goods{i}.jpg")
        if os.path.exists(img_file):
            img = pygame.image.load(img_file)
            img = pygame.transform.scale(img, (GOODS_SIZE, GOODS_SIZE))
            GOODS_IMAGES[GoodsColor(i)] = img
        else:
            print(f"Warning: goods image not found: {img_file}")

# ===============================
# ZONES CLIQUABLES (exportées)
# ===============================
DEPOT_RECTS = {}      # depot_id -> Rect
DEPOT_HEXES = {}      # (depot_id, index) -> dict
BLACK_DEPOT_RECT = None


def draw_central_board(screen, board, origin, mouse_pos=None, selected_tile=None):
    """
    Dessine le plateau central :
    - dépôts 1 à 6
    - tuiles hexagonales dans chaque dépôt
    - marchandises (goods) sous chaque dépôt
    - dépôt noir
    Met à jour les zones cliquables.
    """
    global DEPOT_RECTS, DEPOT_HEXES, BLACK_DEPOT_RECT

    # Load goods images if not already loaded
    load_goods_images()

    DEPOT_RECTS.clear()
    DEPOT_HEXES.clear()

    ox, oy = origin
    font = pygame.font.SysFont(None, 24)

    # ===============================
    # DEPOTS 1 À 6
    # ===============================
    for depot_id in range(1, 7):
        x = ox + (depot_id - 1) * (DEPOT_WIDTH + DEPOT_GAP)
        y = oy

        depot_rect = pygame.Rect(x, y, DEPOT_WIDTH, DEPOT_HEIGHT)
        DEPOT_RECTS[depot_id] = depot_rect

        # fond dépôt
        pygame.draw.rect(screen, (70, 70, 70), depot_rect, border_radius=8)
        pygame.draw.rect(screen, (160, 160, 160), depot_rect, 2, border_radius=8)

        # numéro dépôt
        txt = font.render(str(depot_id), True, (255, 255, 255))
        screen.blit(txt, (x + 6, y + 6))

        # ===============================
        # TUILES HEXAGONALES
        # ===============================
        tiles = board.depots[depot_id]

        for i, tile in enumerate(tiles):
            hx = x + DEPOT_WIDTH // 2
            hy = y + 40 + i * (HEX_SIZE * 1.7)

            rect = pygame.Rect(
                hx - HEX_SIZE,
                hy - HEX_SIZE,
                HEX_SIZE * 2,
                HEX_SIZE * 2,
            )

            is_hovered = mouse_pos and rect.collidepoint(mouse_pos)
            is_selected = selected_tile == (depot_id, i)

            base_color = TILE_COLORS.get(tile.tile_type, (150, 150, 150))

            # couleur boostée si hover
            if is_hovered:
                color = (
                    min(base_color[0] + 40, 255),
                    min(base_color[1] + 40, 255),
                    min(base_color[2] + 40, 255),
                )
            else:
                color = base_color

            # hexagone
            draw_hex(screen, (hx, hy), color)

            # contour sélection
            if is_selected:
                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (hx, hy),
                    HEX_SIZE + 4,
                    2,
                )

            DEPOT_HEXES[(depot_id, i)] = {
                "rect": rect,
                "tile": tile,
            }

        # ===============================
        # MARCHANDISES (GOODS) SOUS LE DEPOT
        # ===============================
        if hasattr(board, 'depot_goods') and depot_id in board.depot_goods:
            goods_list = board.depot_goods[depot_id]
            goods_y = y + DEPOT_HEIGHT + 5  # Position below the depot
            
            for gi, goods_tile in enumerate(goods_list):
                goods_x = x + 10 + gi * (GOODS_SIZE + 4)
                
                # Draw the goods image if available
                if goods_tile.color in GOODS_IMAGES:
                    screen.blit(GOODS_IMAGES[goods_tile.color], (goods_x, goods_y))
                else:
                    # Fallback: draw a colored square
                    color_value = goods_tile.color.value
                    fallback_colors = {
                        1: (200, 100, 100),  # Red-ish
                        2: (100, 200, 100),  # Green-ish
                        3: (100, 100, 200),  # Blue-ish
                        4: (200, 200, 100),  # Yellow-ish
                        5: (200, 100, 200),  # Purple-ish
                        6: (100, 200, 200),  # Cyan-ish
                    }
                    fallback_color = fallback_colors.get(color_value, (150, 150, 150))
                    pygame.draw.rect(screen, fallback_color, 
                                    (goods_x, goods_y, GOODS_SIZE, GOODS_SIZE))
                    pygame.draw.rect(screen, (255, 255, 255), 
                                    (goods_x, goods_y, GOODS_SIZE, GOODS_SIZE), 1)

    # ===============================
    # DEPOT NOIR
    # ===============================
    bx = ox + 6 * (DEPOT_WIDTH + DEPOT_GAP) + 40
    by = oy

    BLACK_DEPOT_RECT = pygame.Rect(bx, by, DEPOT_WIDTH, DEPOT_HEIGHT)
    black_hover = mouse_pos and BLACK_DEPOT_RECT.collidepoint(mouse_pos)

    pygame.draw.rect(screen, (30, 30, 30), BLACK_DEPOT_RECT, border_radius=8)
    pygame.draw.rect(
        screen,
        (255, 255, 255) if black_hover else (255, 215, 0),
        BLACK_DEPOT_RECT,
        2,
        border_radius=8,
    )

    black_txt = font.render("Noir", True, (255, 215, 0))
    screen.blit(
        black_txt,
        (
            bx + BLACK_DEPOT_RECT.width // 2 - black_txt.get_width() // 2,
            by + 45,
        ),
    )

def draw_steps(screen, players, origin):
    ox, oy = origin

    STEP_RADIUS = 22
    STEP_GAP = 90
    PION_RADIUS = 8
    FONT = pygame.font.SysFont(None, 22)

    centers = {}

    # --- Marches 1 à 6 ---
    for step in range(1, 7):
        cx = ox + (step - 1) * STEP_GAP
        cy = oy
        centers[step] = (cx, cy)

        pygame.draw.circle(screen, (50, 50, 50), (cx, cy), STEP_RADIUS)
        pygame.draw.circle(screen, (180, 180, 180), (cx, cy), STEP_RADIUS, 3)

        txt = FONT.render(str(step), True, (255, 255, 255))
        screen.blit(
            txt,
            (cx - txt.get_width() // 2, cy - txt.get_height() // 2)
        )

    # --- Pions joueurs ---
    for step in range(1, 7):
        cx, cy = centers[step]
        players_here = [p for p in players if p.step_position == step]

        for i, p in enumerate(players_here):
            py = cy + STEP_RADIUS + 14 + i * (PION_RADIUS * 2 + 4)
            px = cx

            pygame.draw.circle(screen, p.color, (px, py), PION_RADIUS)

            # contour blanc pour le joueur actif
            if p.is_active:
                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (px, py),
                    PION_RADIUS + 2,
                    2,
                )


