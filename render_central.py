import pygame
from render_hex import draw_hex
from board import TileType

# ===============================
# CONSTANTES VISUELLES
# ===============================
DEPOT_WIDTH = 140
DEPOT_HEIGHT = 140
DEPOT_GAP = 18

HEX_SIZE = 20      
HEX_GAP = 12         # espace réel entre hex

STEP_RADIUS = 22
STEP_GAP = 90
STEP_RECTS = {}

TILE_COLORS = {
    TileType.CASTLE: (200, 200, 200),
    TileType.BUILDING: (200, 150, 80),
    TileType.SHIP: (80, 140, 220),
    TileType.MINE: (120, 120, 120),
    TileType.ANIMAL: (120, 200, 120),
    TileType.KNOWLEDGE: (170, 120, 200),
}

# ===============================
# ZONES CLIQUABLES
# ===============================
DEPOT_RECTS = {}
DEPOT_HEXES = {}
BLACK_DEPOT_RECT = None


def draw_central_board(screen, board, origin, mouse_pos=None, selected_tile=None):
    """
    Plateau central :
    - 6 dépôts (grille 2x2)
    - hex petits et espacés
    - dépôt noir visible
    """
    global DEPOT_RECTS, DEPOT_HEXES, BLACK_DEPOT_RECT

    DEPOT_RECTS.clear()
    DEPOT_HEXES.clear()

    ox, oy = origin
    font = pygame.font.SysFont(None, 24)

    # ===============================
    # DEPOTS 1 → 6
    # ===============================
    for depot_id in range(1, 7):
        x = ox + (depot_id - 1) * (DEPOT_WIDTH + DEPOT_GAP)
        y = oy

        depot_rect = pygame.Rect(x, y, DEPOT_WIDTH, DEPOT_HEIGHT)
        DEPOT_RECTS[depot_id] = depot_rect

        pygame.draw.rect(screen, (70, 70, 70), depot_rect, border_radius=8)
        pygame.draw.rect(screen, (160, 160, 160), depot_rect, 2, border_radius=8)

        txt = font.render(str(depot_id), True, (255, 255, 255))
        screen.blit(txt, (x + 6, y + 6))

        # ===============================
        # TUILES — GRILLE 2x2
        # ===============================
        tiles = board.depots.get(depot_id, [])

        COLS = 2
        cell = HEX_SIZE * 2 + HEX_GAP

        grid_width = COLS * cell - HEX_GAP
        start_x = x + (DEPOT_WIDTH - grid_width) // 2 + HEX_SIZE
        start_y = y + 36

        for i, tile in enumerate(tiles[:4]):  # max 4 visibles
            col = i % COLS
            row = i // COLS

            hx = start_x + col * cell
            hy = start_y + row * cell

            rect = pygame.Rect(
                hx - HEX_SIZE,
                hy - HEX_SIZE,
                HEX_SIZE * 2,
                HEX_SIZE * 2,
            )

            is_hovered = mouse_pos and rect.collidepoint(mouse_pos)
            is_selected = selected_tile == (depot_id, i)

            base_color = TILE_COLORS.get(tile.tile_type, (150, 150, 150))
            color = (
                min(base_color[0] + 40, 255),
                min(base_color[1] + 40, 255),
                min(base_color[2] + 40, 255),
            ) if is_hovered else base_color

            draw_hex(screen, (hx, hy), color, HEX_SIZE)

            if is_selected:
                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (hx, hy),
                    HEX_SIZE + 3,
                    2,
                )

            DEPOT_HEXES[(depot_id, i)] = {
                "rect": rect,
                "tile": tile,
            }

    # ===============================
    # DEPOT NOIR (collé au dépôt 6)
    # ===============================
    last = DEPOT_RECTS[6]
    bx = last.right + 24
    by = last.top

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

    txt = font.render("Noir", True, (255, 215, 0))
    screen.blit(
        txt,
        (
            bx + DEPOT_WIDTH // 2 - txt.get_width() // 2,
            by + DEPOT_HEIGHT // 2 - txt.get_height() // 2,
        ),
    )


def draw_steps(screen, players, origin):
    ox, oy = origin
    FONT = pygame.font.SysFont(None, 22)
    centers = {}

    for step in range(1, 7):
        cx = ox + (step - 1) * STEP_GAP
        cy = oy
        centers[step] = (cx, cy)

        pygame.draw.circle(screen, (50, 50, 50), (cx, cy), STEP_RADIUS)
        pygame.draw.circle(screen, (180, 180, 180), (cx, cy), STEP_RADIUS, 3)

        txt = FONT.render(str(step), True, (255, 255, 255))
        screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    for step, (cx, cy) in centers.items():
        players_here = [p for p in players if p.step_position == step]
        for i, p in enumerate(players_here):
            py = cy + STEP_RADIUS + 14 + i * 18
            pygame.draw.circle(screen, p.color, (cx, py), 8)
            if p.is_active:
                pygame.draw.circle(screen, (255, 255, 255), (cx, py), 10, 2)
