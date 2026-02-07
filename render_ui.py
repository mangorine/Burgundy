# render_ui.py
import pygame

def draw_button(screen, rect, text, font, *, fill=(70,70,70), border=(200,200,200), text_color=(255,255,255), active=False):
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    pygame.draw.rect(screen, (255,255,255) if active else border, rect, 2, border_radius=10)
    txt = font.render(text, True, text_color)
    screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

def draw_panel(screen, rect, *, fill=(35,35,35), border=(160,160,160)):
    pygame.draw.rect(screen, fill, rect, border_radius=12)
    pygame.draw.rect(screen, border, rect, 2, border_radius=12)

def draw_die(screen, center, value, font, *, size=54, fill=(240,240,240), pip=(20,20,20)):
    # carré arrondi
    rect = pygame.Rect(0,0,size,size)
    rect.center = center
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    pygame.draw.rect(screen, (40,40,40), rect, 2, border_radius=10)

    # Dessiner les points du dé (pips)
    pip_radius = size // 10  # Taille des points proportionnelle au dé
    margin = size // 4       # Marge depuis le bord
    
    # Positions des points (relatif au centre du dé)
    cx, cy = center
    left = cx - margin
    right = cx + margin
    top = cy - margin
    bottom = cy + margin
    mid_x = cx
    mid_y = cy
    
    # Patterns des points selon la valeur
    pip_positions = {
        1: [(mid_x, mid_y)],
        2: [(left, top), (right, bottom)],
        3: [(left, top), (mid_x, mid_y), (right, bottom)],
        4: [(left, top), (right, top), (left, bottom), (right, bottom)],
        5: [(left, top), (right, top), (mid_x, mid_y), (left, bottom), (right, bottom)],
        6: [(left, top), (right, top), (left, mid_y), (right, mid_y), (left, bottom), (right, bottom)],
    }
    
    # Dessiner chaque point
    positions = pip_positions.get(value, [])
    for pos in positions:
        pygame.draw.circle(screen, pip, pos, pip_radius)

def draw_toast(screen, rect, message, font, *, fill=(20,20,20), border=(255,220,120), text_color=(255,220,120)):
    pygame.draw.rect(screen, fill, rect, border_radius=12)
    pygame.draw.rect(screen, border, rect, 2, border_radius=12)
    txt = font.render(message, True, text_color)
    screen.blit(txt, (rect.x + 14, rect.y + rect.height//2 - txt.get_height()//2))
