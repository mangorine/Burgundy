
# ui/colors.py
from board import TileType

TILE_COLORS = {
    TileType.CASTLE:   (0, 86, 27),   # vert fonce
    TileType.BUILDING: (136, 66, 29),    # marron
    TileType.ANIMAL:   (0, 255, 0),     # vert
    TileType.MINE:     (70, 70, 70),       # gris foncé
    TileType.KNOWLEDGE:(255, 255, 0),    # jaune
    TileType.SHIP:     (100, 190, 210),    # cyan
}

EMPTY_COLOR = (40, 40, 40)
BORDER_COLOR = (15, 15, 15)
BACKGROUND_COLOR = (25, 25, 25)
