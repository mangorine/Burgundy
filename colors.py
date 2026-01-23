
# ui/colors.py
from board import TileType, GoodsColor

TILE_COLORS = {
    TileType.CASTLE:   (0, 86, 27),   # vert fonce
    TileType.BUILDING: (255, 140, 0),    # orange
    TileType.ANIMAL:   (0, 255, 0),     # vert
    TileType.MINE:     (150, 150, 150),       # gris foncé
    TileType.KNOWLEDGE:(255, 255, 0),    # jaune
    TileType.SHIP:     (100, 190, 210),    # cyan
}

# Couleurs des marchandises (tuiles carrées)
GOODS_COLORS = {
    GoodsColor.COLOR_1: (139, 69, 19),    # Marron (bois)
    GoodsColor.COLOR_2: (70, 130, 180),   # Bleu acier (poisson)
    GoodsColor.COLOR_3: (178, 34, 34),    # Rouge brique (vin)
    GoodsColor.COLOR_4: (218, 165, 32),   # Or (céréales)
    GoodsColor.COLOR_5: (128, 0, 128),    # Violet (tissu)
    GoodsColor.COLOR_6: (34, 139, 34),    # Vert forêt (bétail)
}

EMPTY_COLOR = (40, 40, 40)
BORDER_COLOR = (15, 15, 15)
BACKGROUND_COLOR = (25, 25, 25)
