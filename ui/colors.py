
# ui/colors.py
from board import TileType

TILE_COLORS = {
    TileType.CASTLE:   (200, 200, 200),   # gris clair
    TileType.BUILDING: (60, 120, 220),    # bleu
    TileType.ANIMAL:   (90, 170, 90),     # vert
    TileType.MINE:     (70, 70, 70),       # gris foncé
    TileType.KNOWLEDGE:(170, 110, 170),    # violet
    TileType.SHIP:     (100, 190, 210),    # cyan
}

EMPTY_COLOR = (40, 40, 40)
BORDER_COLOR = (15, 15, 15)
BACKGROUND_COLOR = (25, 25, 25)
