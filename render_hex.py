# ui/render_hex.py
import math
import pygame
import os

from colors import TILE_COLORS, EMPTY_COLOR, BORDER_COLOR, GOODS_COLORS
from board import TileType, GoodsColor  # important pour tester BUILDING/ANIMAL/...

HEX_SIZE = 40
SQRT3 = math.sqrt(3)

IMAGE_CACHE = {}
IMAGE_DIRS = (
    "images",
    os.path.join("images", "buildings"),
    os.path.join("images", "animals"),
    os.path.join("images", "knowledge"),
    os.path.join("images", "goods"),
)
GENERIC_TILE_IMAGES = {
    TileType.BUILDING: "cloister-building",
    TileType.ANIMAL: "cloister-livestock",
    TileType.SHIP: "cloister-ship",
    TileType.MINE: "cloister-mine",
    TileType.CASTLE: "cloister-castle",
    TileType.KNOWLEDGE: "cloister-knowledge",
}

# Cache pour les images de marchandises
GOODS_IMAGE_CACHE = {}

def get_goods_image(goods_color: GoodsColor):
    """
    Charge et retourne l'image de la marchandise correspondant à la couleur.
    Les images sont dans images/goods/goodsN.jpg où N = 1-6
    """
    if goods_color in GOODS_IMAGE_CACHE:
        return GOODS_IMAGE_CACHE[goods_color]
    
    # Le numéro correspond à la valeur de l'enum (COLOR_1 = 1, etc.)
    color_num = goods_color.value
    filename = f"goods{color_num}.jpg"
    filepath = os.path.join("images", "goods", filename)
    
    if os.path.exists(filepath):
        try:
            img = pygame.image.load(filepath).convert()
            GOODS_IMAGE_CACHE[goods_color] = img
            return img
        except Exception:
            pass
    
    GOODS_IMAGE_CACHE[goods_color] = None
    return None

def _find_image_path(base_name: str):
    """Cherche <base_name>.(png|jpg|jpeg) dans les dossiers d'images connus."""
    for directory in IMAGE_DIRS:
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join(directory, base_name + ext)
            if os.path.exists(path):
                return path
    return None

def _normalize_name(raw_name: str) -> str:
    return raw_name.lower().replace("'", "").replace(" ", "-")

def _animal_image_name(animal_type: str) -> str:
    if animal_type in {"pig", "chicken", "goat"}:
        return f"{animal_type}s"
    return animal_type

def get_tile_image(tile_or_type):
    """
    Accepte:
    - un Tile (avec .tile_type + .tile)
    - ou un TileType (fallback)
    Retourne une surface pygame ou None.
    """
    if tile_or_type is None:
        return None

    base_name = None

    #  Cas 1 : objet Tile complet 
    if hasattr(tile_or_type, "tile_type"):
        t = tile_or_type
        ttype = t.tile_type

        # BUILDING -> nom du building_type: bank, church, city-hall, ...
        if ttype == TileType.BUILDING and hasattr(t, "tile") and hasattr(t.tile, "building_type"):
            raw_name = str(getattr(t.tile.building_type, "value", t.tile.building_type.name))
            base_name = _normalize_name(raw_name)

        # ANIMAL -> ex: 2cattle, 3pigs ...
        elif ttype == TileType.ANIMAL and hasattr(t, "tile") and hasattr(t.tile, "animal_type"):
            count = getattr(t.tile, "count", 1)
            atype = str(t.tile.animal_type.name).lower()
            base_name = f"{count}{_animal_image_name(atype)}"

        # SHIP/MINE -> fichiers ship.png / mine.png
        elif ttype == TileType.SHIP:
            base_name = "ship"
        elif ttype == TileType.MINE:
            base_name = "mine"
        elif ttype == TileType.KNOWLEDGE and hasattr(t, "tile") and hasattr(t.tile, "tile_id"):
            base_name = f"knowledge{t.tile.tile_id}"

        # CASTLE / KNOWLEDGE / autres -> castle, knowledge, ...
        else:
            base_name = str(ttype.name).lower()

    #  Cas 2 : juste un TileType 
    elif hasattr(tile_or_type, "name"):
        base_name = str(tile_or_type.name).lower()

    else:
        base_name = str(tile_or_type).lower()

    if base_name in IMAGE_CACHE:
        return IMAGE_CACHE[base_name]

    path = _find_image_path(base_name)
    if not path:
        ttype = None
        if hasattr(tile_or_type, "tile_type"):
            ttype = tile_or_type.tile_type
        elif isinstance(tile_or_type, TileType):
            ttype = tile_or_type

        if ttype in GENERIC_TILE_IMAGES:
            fallback_name = GENERIC_TILE_IMAGES[ttype]
            path = _find_image_path(fallback_name)

        if not path:
            IMAGE_CACHE[base_name] = None
            return None

    # png => alpha
    if path.lower().endswith(".png"):
        img = pygame.image.load(path).convert_alpha()
    else:
        img = pygame.image.load(path).convert()

    IMAGE_CACHE[base_name] = img
    return img


def axial_to_pixel(q, r, origin):
    ox, oy = origin
    x = HEX_SIZE * (SQRT3 * q + (SQRT3 / 2) * r) + ox
    y = HEX_SIZE * (1.5 * r) + oy
    return (x, y)

def hex_corners(center, size):
    cx, cy = center
    corners = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx + size * math.cos(angle)
        y = cy + size * math.sin(angle)
        corners.append((x, y))
    return corners

def get_masked_hex_image(image, size):
    surf_size = int(size * 2)
    temp_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    temp_surf.fill((0, 0, 0, 0))

    local_center = (size, size)
    points = hex_corners(local_center, size)
    pygame.draw.polygon(temp_surf, (255, 255, 255, 255), points)

    img_scaled = pygame.transform.smoothscale(image, (surf_size, surf_size))

    # IMPORTANT: pour garder la transparence correctement, on utilise BLEND_RGBA_MULT
    # avec un masque déjà présent en alpha.
    # Technique simple: on blit l'image puis on "coupe" via le masque alpha.
    # On fait l’inverse: on crée un surf, on met l’image, puis on applique le masque alpha.
    img_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    img_surf.blit(img_scaled, (0, 0))
    img_surf.blit(temp_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return img_surf

def draw_hex(surface, center, fill_color, size, tile=None):
    points = hex_corners(center, size)

    # fond
    pygame.draw.polygon(surface, fill_color, points)

    # image (si dispo)
    img = get_tile_image(tile)
    if img:
        hex_img = get_masked_hex_image(img, size)
        rect = hex_img.get_rect(center=center)
        surface.blit(hex_img, rect)

    # bordure
    pygame.draw.polygon(surface, BORDER_COLOR, points, 2)

def draw_player_board(surface, player_board, origin, font_debug, selected_hex=None, legal_coords=None):
    for (q, r), slot in player_board.hex_map.grid.items():
        center = axial_to_pixel(q, r, origin)
        base_color = TILE_COLORS.get(slot.allowed_type, EMPTY_COLOR)

        # Tuile / case 
        if slot.is_occupied:
            draw_hex(surface, center, base_color, HEX_SIZE, slot.tile)
        else:
            empty_fill = [max(0, c - 40) for c in base_color]
            draw_hex(surface, center, empty_fill, HEX_SIZE)

        # HIGHLIGHT COUPS LÉGAUX
        if legal_coords and (q, r) in legal_coords:
            points = hex_corners(center, HEX_SIZE)
            pygame.draw.polygon(surface, (0, 255, 0), points, 3)

        #  SÉLECTION 
        if selected_hex == (q, r):
            pygame.draw.circle(surface, (255, 255, 0), center, 6)

     # DEBUG : afficher coordonnées et valeur du slot
   #  AFFICHAGE DE LA VALEUR DE DÉ DE LA CASE 
        if font_debug and slot.dice_value is not None:
            label = font_debug.render(str(slot.dice_value), True, (255, 255, 255))
            label_rect = label.get_rect(center=(center[0], center[1] + 14))
            surface.blit(label, label_rect)
def draw_storage(surface, storage, selected_index, origin):
    x0, y0 = origin
    SLOT_SIZE = 50
    GAP = 20

    for i in range(3):
        x = x0 + i * (SLOT_SIZE + GAP)
        y = y0
        rect = pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

        pygame.draw.rect(surface, (60, 60, 60), rect, border_radius=8)
        pygame.draw.rect(surface, (30, 30, 30), rect, 2, border_radius=8)

        if selected_index == i:
            pygame.draw.rect(surface, (255, 255, 0), rect, 3, border_radius=8)

        if i < len(storage):
            tile = storage[i]
            if tile is not None:
                img = get_tile_image(tile)
                if img:
                    hex_img = get_masked_hex_image(img, (SLOT_SIZE - 10) // 2)
                    surface.blit(hex_img, hex_img.get_rect(center=rect.center))
                else:
                    pygame.draw.circle(surface, (200, 200, 200), rect.center, 18)

def cube_round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
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
    q = (SQRT3 / 3) * x - (1 / 3) * y
    r = (2 / 3) * y
    rx, ry, rz = cube_round(q, -q - r, r)
    return (rx, rz)


def draw_goods_storage(surface, goods_list, origin, font=None):
    """
    Affiche les marchandises du joueur, groupées par couleur.
    Utilise les images de images/goods/goodsN.jpg
    Max 3 couleurs différentes (règle du jeu).
    """
    x0, y0 = origin
    GOODS_SIZE = 28
    GAP_X = 35  # Espace entre les colonnes de couleurs
    GAP_Y = 4   # Espace vertical entre les carrés de même couleur
    
    # Grouper les marchandises par couleur
    goods_by_color = {}
    for g in goods_list:
        color = g.color
        if color not in goods_by_color:
            goods_by_color[color] = []
        goods_by_color[color].append(g)
    
    # Titre
    if font:
        title = font.render("MARCHANDISES", True, (200, 200, 200))
        surface.blit(title, (x0, y0 - 22))
    
    # Fond de la zone
    num_colors = max(len(goods_by_color), 3)  # Au moins 3 colonnes
    total_width = num_colors * GAP_X + 10
    max_stack = max([len(v) for v in goods_by_color.values()]) if goods_by_color else 1
    total_height = max_stack * (GOODS_SIZE + GAP_Y) + 10
    
    bg_rect = pygame.Rect(x0 - 5, y0, total_width, total_height)
    pygame.draw.rect(surface, (40, 35, 30), bg_rect, border_radius=8)
    pygame.draw.rect(surface, (80, 70, 60), bg_rect, 2, border_radius=8)
    
    # Dessiner chaque colonne de marchandises
    col = 0
    for color_enum, goods in goods_by_color.items():
        # Charger l'image de la marchandise
        goods_img = get_goods_image(color_enum)
        fallback_color = GOODS_COLORS.get(color_enum, (150, 150, 150))
        
        for i, g in enumerate(goods):
            gx = x0 + col * GAP_X + 5
            gy = y0 + 5 + i * (GOODS_SIZE + GAP_Y)
            
            rect = pygame.Rect(gx, gy, GOODS_SIZE, GOODS_SIZE)
            
            if goods_img:
                # Redimensionner et afficher l'image
                img_scaled = pygame.transform.smoothscale(goods_img, (GOODS_SIZE, GOODS_SIZE))
                surface.blit(img_scaled, (gx, gy))
                pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=4)
            else:
                # Fallback: carré coloré
                pygame.draw.rect(surface, fallback_color, rect, border_radius=4)
                pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=4)
        
        col += 1
    
    # Si pas de marchandises, afficher "(vide)"
    if not goods_by_color:
        if font:
            empty_txt = font.render("(vide)", True, (100, 100, 100))
            surface.blit(empty_txt, (x0 + 10, y0 + 15))
