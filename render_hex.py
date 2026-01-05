# ui/render_hex.py
import math
import pygame
from colors import TILE_COLORS, EMPTY_COLOR, BORDER_COLOR


HEX_SIZE = 40  # rayon d'un hexagone
SQRT3 = math.sqrt(3)

def axial_to_pixel(q, r, origin):
    """Convertit (q,r) -> (x,y)"""
    ox, oy = origin
    x = HEX_SIZE * (SQRT3 * q + (SQRT3 / 2) * r) + ox
    y = HEX_SIZE * (1.5 * r) + oy
    return (x, y)

def hex_corners(center):
    """Retourne les 6 sommets d'un hexagone"""
    cx, cy = center
    corners = []
    for i in range(6):
        angle = math.radians(60 * i - 30)  # pointy-top
        x = cx + HEX_SIZE * math.cos(angle)
        y = cy + HEX_SIZE * math.sin(angle)
        corners.append((x, y))
    return corners

def draw_hex(surface, center, fill_color):
    points = hex_corners(center)
    pygame.draw.polygon(surface, fill_color, points)
    pygame.draw.polygon(surface, BORDER_COLOR, points, 2)

def draw_player_board(surface, player_board, origin, selected_hex=None, legal_coords=None):
    for (q, r), slot in player_board.hex_map.grid.items():
        center = axial_to_pixel(q, r, origin)
        color = TILE_COLORS.get(slot.allowed_type, EMPTY_COLOR)

        draw_hex(surface, center, color)
        if legal_coords and (q, r) in legal_coords:
            pygame.draw.circle(surface, (0, 255, 0), center, 8)


        if selected_hex == (q, r):
            pygame.draw.circle(surface, (255, 255, 0), center, 6)

def cube_round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)

    dx = abs(rx - x)
    dy = abs(ry - y)
    dz = abs(rz - z)

    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry

    return rx, ry, rz


def pixel_to_axial(px, py, origin):
    ox, oy = origin
    x = (px - ox) / HEX_SIZE
    y = (py - oy) / HEX_SIZE

    # inverse pointy-top
    q = (SQRT3 / 3) * x - (1 / 3) * y
    r = (2 / 3) * y

    # axial → cube
    cx = q
    cz = r
    cy = -cx - cz

    rx, ry, rz = cube_round(cx, cy, cz)

    # cube → axial
    return (rx, rz)
def draw_storage(surface, storage, selected_index, origin):
    x0, y0 = origin
    SLOT_SIZE = 50
    GAP = 20

    for i in range(3):
        x = x0 + i * (SLOT_SIZE + GAP)
        y = y0
        rect = pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

        # fond
        pygame.draw.rect(surface, (80, 80, 80), rect, border_radius=8)
        pygame.draw.rect(surface, (30, 30, 30), rect, 2, border_radius=8)

        # sélection
        if selected_index == i:
            pygame.draw.rect(surface, (255, 255, 0), rect, 3, border_radius=8)

        # tuile (SEULEMENT si elle existe)
        if i < len(storage):
            tile = storage[i]
            if tile is not None:
                pygame.draw.circle(surface, (200, 200, 200), rect.center, 18)
