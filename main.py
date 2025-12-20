import pygame
import collections
import sys
import os
import math

pygame.init()
WIDTH = 900
HEIGHT = 650
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("BlackKnight Puzzle")

# -------------------------
# Resource helper for PyInstaller compatibility
# -------------------------
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller onefile.
    relative_path: path relative to project root, e.g. "build/web/assets/images/black knight.png"
    """
    relative_path = os.path.normpath(relative_path)
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Try to load a bundled font; fallback to default
def load_font(path, size):
    try:
        full = resource_path(path)
        return pygame.font.Font(full, size)
    except Exception:
        return pygame.font.Font(None, size)

small_font = load_font("build/web/assets/Blacknorthdemo-mLE25.ttf", 20)
big_font = load_font("build/web/assets/Blacknorthdemo-mLE25.ttf", 48)
tiny_font = load_font("build/web/assets/Blacknorthdemo-mLE25.ttf", 16)
medium_font = load_font("build/web/assets/Blacknorthdemo-mLE25.ttf", 28)

timer = pygame.time.Clock()
fps = 60

# Level definitions
LEVELS = [
    {
        'name': 'Tutorial',
        'white_pieces': ['rook', 'bishop'],
        'white_locations': [(2, 0), (3, 0)],
        'black_start': (0, 0),
        'target': (5, 2),
        'optimal_moves': 8,
        'description': 'Learn to move the knight',
        'tutorial_text': 'Move white pieces to create a path for the black knight'
    },
    {
        'name': 'Easy',
        'white_pieces': ['bishop', 'bishop', 'rook', 'knight'],
        'white_locations': [(1, 0), (2, 0), (3, 0), (4, 0)],
        'black_start': (0, 0),
        'target': (5, 2),
        'optimal_moves': 12,
        'description': 'Navigate around more pieces',
        'tutorial_text': 'Plan your moves - white pieces block the knight\'s path'
    },
    {
        'name': 'Medium',
        'white_pieces': ['bishop', 'bishop', 'rook', 'knight', 'knight', 'rook'],
        'white_locations': [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (4, 0)],
        'black_start': (0, 0),
        'target': (5, 2),
        'optimal_moves': 15,
        'description': 'A trickier puzzle awaits',
        'tutorial_text': 'Think ahead - multiple pieces need repositioning'
    },
    {
        'name': 'Hard',
        'white_pieces': ['bishop', 'bishop', 'bishop', 'bishop', 'rook', 'knight', 'knight', 'knight', 'knight', 'rook', 'rook', 'rook'],
        'white_locations': [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (4, 2)],
        'black_start': (0, 0),
        'target': (5, 2),
        'optimal_moves': 18,
        'description': 'The ultimate challenge',
        'tutorial_text': 'Master puzzle! Use the hint if you get stuck.'
    }
]

# Game state
current_level = 0
game_state = 'menu'  # 'menu', 'playing', 'level_complete', 'game_complete'
white_pieces = []
white_locations = []
black_pieces = ['knight']
black_locations = []
selection = None
valid_moves = []
move_count = 0
winner = ""
game_history = []
level_stats = [{} for _ in LEVELS]  # Stats for each level

hint_piece = None
hint_move = None
hint_show_time = 0

# Animation state
animating = False
anim_info = None

# UI state
ui_pulse = 0
button_feedback = {'play': 0, 'hint': 0}
show_tutorial = False
particles = []

# Load and scale images with safe fallback
def load_image(path, size):
    try:
        full = resource_path(path)
        img = pygame.image.load(full).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((180, 180, 180, 255))
        pygame.draw.rect(surf, (100, 100, 100), surf.get_rect(), 3)
        return surf

black_knight = load_image('build/web/assets/images/black knight.png', (80, 80))
white_rook = load_image('build/web/assets/images/white rook.png', (80, 80))
white_knight = load_image('build/web/assets/images/white knight.png', (80, 80))
white_bishop = load_image('build/web/assets/images/white bishop.png', (80, 80))

white_images = {
    'knight': white_knight,
    'bishop': white_bishop,
    'rook': white_rook
}
black_images = {
    'knight': black_knight
}

# Colors
BACKGROUND_COLOR = (35, 40, 50)
BOARD_LIGHT = (210, 215, 225)
BOARD_DARK = (110, 120, 140)
TEXT_COLOR = (255, 255, 255)
BUTTON_HOVER = (80, 130, 220)
BUTTON_NORMAL = (60, 100, 180)
BUTTON_ACCENT = (70, 180, 80)
BUTTON_ACCENT_HOVER = (90, 210, 100)
BUTTON_DANGER = (180, 70, 70)
BUTTON_DANGER_HOVER = (220, 100, 100)
BUTTON_EXIT = (100, 100, 110)
BUTTON_EXIT_HOVER = (130, 130, 140)
BUTTON_DISABLED = (60, 60, 70)
ACCENT_COLOR = (255, 200, 80)
MENU_BG = (25, 30, 40)

BOARD_ORIGIN = (0, 0)
SQUARE_SIZE = 100

# Particle class for visual effects
class Particle:
    def __init__(self, x, y, color, vx, vy):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.life = 60
        self.size = 8
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
        self.size = max(1, self.size * 0.95)
        return self.life > 0
    
    def draw(self):
        alpha = int(255 * (self.life / 60))
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))

def spawn_particles(x, y, color, count=10):
    for _ in range(count):
        angle = math.radians(pygame.time.get_ticks() % 360 + _ * 36)
        speed = 3 + _ * 0.5
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 3
        particles.append(Particle(x, y, color, vx, vy))

def is_on_board(position):
    x, y = position
    if y < 2:
        return 0 <= x <= 5
    elif y == 2:
        return 4 <= x <= 5
    return False

def draw_board():
    for row in range(3):
        for col in range(6):
            if row < 2 or (row == 2 and col >= 4):
                color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
                pygame.draw.rect(screen, color, [col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE])
    
    # target highlight with glow effect
    t = pygame.time.get_ticks() / 500.0
    glow = int(30 + 20 * math.sin(t))
    pygame.draw.rect(screen, (180 - glow, 230, 230), [5 * SQUARE_SIZE, 2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE])
    pygame.draw.rect(screen, (150, 255, 255), [5 * SQUARE_SIZE, 2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE], 3)

def draw_pieces():
    # white pieces
    for i, (piece, loc) in enumerate(zip(white_pieces, white_locations)):
        img = white_images.get(piece, white_knight)
        draw_x, draw_y = loc[0] * SQUARE_SIZE + 10, loc[1] * SQUARE_SIZE + 10
        if animating and anim_info and anim_info['piece_type']=='white' and anim_info['index']==i:
            continue
        
        if selection == i:
            scaled = pygame.transform.smoothscale(img, (90, 90))
            screen.blit(scaled, (draw_x - 5, draw_y - 5))
        else:
            screen.blit(img, (draw_x, draw_y))
        
        if selection == i:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            t = pygame.time.get_ticks() / 300.0
            alpha = int(100 + 50 * math.sin(t))
            s.fill((255, 255, 0, alpha))
            screen.blit(s, (loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE))
            pygame.draw.rect(screen, (255, 255, 100, 255), [loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE], 2)

    # black pieces
    for i, (piece, loc) in enumerate(zip(black_pieces, black_locations)):
        img = black_images.get(piece, black_knight)
        draw_x, draw_y = loc[0] * SQUARE_SIZE + 10, loc[1] * SQUARE_SIZE + 10
        if animating and anim_info and anim_info['piece_type']=='black' and anim_info['index']==i:
            continue
        
        if selection == i + len(white_pieces):
            scaled = pygame.transform.smoothscale(img, (90, 90))
            screen.blit(scaled, (draw_x - 5, draw_y - 5))
        else:
            screen.blit(img, (draw_x, draw_y))
        
        if selection == i + len(white_pieces):
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            t = pygame.time.get_ticks() / 300.0
            alpha = int(100 + 50 * math.sin(t))
            s.fill((255, 255, 0, alpha))
            screen.blit(s, (loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE))
            pygame.draw.rect(screen, (255, 255, 100, 255), [loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE], 2)

def draw_valid(valid_moves):
    t = pygame.time.get_ticks() / 250.0
    radius = 20 + int(8 * (0.5 + 0.5 * math.sin(t)))
    for move in valid_moves:
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 200, 255, 180), (SQUARE_SIZE//2, SQUARE_SIZE//2), radius)
        pygame.draw.circle(s, (200, 255, 255, 200), (SQUARE_SIZE//2, SQUARE_SIZE//2), radius - 3, 2)
        screen.blit(s, (move[0] * SQUARE_SIZE, move[1] * SQUARE_SIZE))

class Button:
    def __init__(self, rect, text, base_color=BUTTON_NORMAL, hover_color=None, font=None, disabled=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color if hover_color else (min(base_color[0]+30, 255), min(base_color[1]+30, 255), min(base_color[2]+30, 255))
        self.hovered = False
        self.pressed = False
        self.press_timer = 0
        self.font = font if font else small_font
        self.disabled = disabled
    
    def draw(self):
        if self.disabled:
            color = BUTTON_DISABLED
        else:
            color = self.hover_color if self.hovered else self.base_color
        
        if self.pressed and not self.disabled:
            self.press_timer -= 1
            press_amount = max(0, self.press_timer / 10.0)
            offset_y = int(press_amount * 3)
        else:
            offset_y = 0
        
        rect = self.rect.copy()
        rect.y += offset_y
        
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=6)
        
        pygame.draw.rect(screen, color, rect, border_radius=6)
        
        if self.disabled:
            pygame.draw.rect(screen, (100, 100, 100), rect, 2, border_radius=6)
        else:
            pygame.draw.rect(screen, (255,255,255), rect, 2, border_radius=6)
        
        text_color = (150, 150, 150) if self.disabled else (255, 255, 255)
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
    
    def update_hover(self, mouse_pos):
        if not self.disabled:
            self.hovered = self.rect.collidepoint(mouse_pos)
        else:
            self.hovered = False
    
    def clicked(self, mouse_pos):
        if self.disabled:
            return False
        if self.rect.collidepoint(mouse_pos):
            self.pressed = True
            self.press_timer = 10
            return True
        return False

# Buttons
play_again_btn = Button((500, 560, 120, 50), "Restart", base_color=BUTTON_DANGER, hover_color=BUTTON_DANGER_HOVER)
hint_btn = Button((350, 560, 120, 50), "Hint", base_color=BUTTON_ACCENT, hover_color=BUTTON_ACCENT_HOVER)
exit_btn = Button((650, 560, 120, 50), "Menu", base_color=BUTTON_EXIT, hover_color=BUTTON_EXIT_HOVER)
next_level_btn = Button((350, 450, 200, 60), "Next Level", base_color=BUTTON_ACCENT, hover_color=BUTTON_ACCENT_HOVER, font=medium_font)
menu_btn = Button((350, 530, 200, 50), "Main Menu", base_color=BUTTON_EXIT, hover_color=BUTTON_EXIT_HOVER)

def draw_game_ui():
    global ui_pulse, hint_btn
    ui_pulse += 1
    
    # bottom panel
    pygame.draw.rect(screen, (25, 30, 40), [0, 300, WIDTH, 350])
    pygame.draw.line(screen, (100, 120, 160), (0, 300), (WIDTH, 300), 2)
    
    # Game title
    screen.blit(big_font.render('Black Knight', True, ACCENT_COLOR), (20, 230))
    
    # Level info
    level = LEVELS[current_level]
    level_text = small_font.render(f"Level: {level['name']}", True, TEXT_COLOR)
    screen.blit(level_text, (20, 320))
    
    # Tutorial text - more helpful instructions
    tutorial_surf = tiny_font.render(level['tutorial_text'], True, (150, 200, 255))
    screen.blit(tutorial_surf, (20, 350))
    
    # Basic instructions
    screen.blit(tiny_font.render('Move the Black Knight to the glowing square! (No captures allowed)', True, (200, 200, 200)), (20, 370))
    screen.blit(tiny_font.render('Click a piece, then click a highlighted square to move it.', True, (180, 180, 180)), (20, 390))
    
    # Only show optimal moves for the last level (Hard)
    if current_level == len(LEVELS) - 1:
        optimal_text = tiny_font.render(f'Optimal solution: {level["optimal_moves"]} moves', True, (150, 200, 255))
        screen.blit(optimal_text, (20, 410))
    
    # Move counter with star rating (only for last level)
    move_text = small_font.render(f'Moves: {move_count}', True, ACCENT_COLOR)
    screen.blit(move_text, (700, 20))
    
    # Star rating preview (only for last level)
    if current_level == len(LEVELS) - 1:
        stars = get_star_rating(move_count, level['optimal_moves'])
        star_y = 50
        for i in range(3):
            color = (255, 215, 0) if i < stars else (80, 80, 80)
            pygame.draw.polygon(screen, color, get_star_points(720 + i * 35, star_y, 12))
    
    # Level progress
    progress_text = tiny_font.render(f'Level {current_level + 1}/{len(LEVELS)}', True, (200, 200, 200))
    screen.blit(progress_text, (700, 90))
    
    # Best score for this level (only show for completed levels)
    if level_stats[current_level].get('completed'):
        best_text = tiny_font.render(f"Personal Best: {level_stats[current_level]['best_moves']} moves", True, (100, 255, 100))
        screen.blit(best_text, (700, 110))
    
    # Credit text
    credit_text = tiny_font.render('Interactive Media class project by', True, (150, 150, 150))
    screen.blit(credit_text, (20, 590))
    credit_name = tiny_font.render('By Youssif Goda for Prof. Russell McDermott', True, (180, 180, 180))
    screen.blit(credit_name, (20, 610))
    
    # Update hint button disabled state - only enabled for last level
    hint_btn.disabled = (current_level != len(LEVELS) - 1)
    
    # buttons
    mouse_pos = pygame.mouse.get_pos()
    play_again_btn.update_hover(mouse_pos)
    hint_btn.update_hover(mouse_pos)
    exit_btn.update_hover(mouse_pos)
    play_again_btn.draw()
    hint_btn.draw()
    exit_btn.draw()

def draw_menu():
    screen.fill(MENU_BG)
    
    # Title with glow effect
    t = pygame.time.get_ticks() / 500.0
    glow = int(20 + 10 * math.sin(t))
    
    title_surf = big_font.render('BLACK KNIGHT PUZZLE', True, ACCENT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 100))
    
    # Draw glow
    for offset in range(glow, 0, -2):
        alpha = int(100 * (1 - offset / glow))
        glow_surf = big_font.render('BLACK KNIGHT PUZZLE', True, (*ACCENT_COLOR[:3], alpha))
        glow_rect = glow_surf.get_rect(center=(WIDTH // 2 + offset // 4, 100 + offset // 4))
    
    screen.blit(title_surf, title_rect)
    
    # Subtitle
    subtitle = small_font.render('Choose Your Challenge', True, TEXT_COLOR)
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 160)))
    
    # Level selection buttons
    mouse_pos = pygame.mouse.get_pos()
    y_start = 220
    level_buttons = []
    
    for i, level in enumerate(LEVELS):
        btn_y = y_start + i * 90
        btn = Button((WIDTH // 2 - 150, btn_y, 300, 70), "", base_color=BUTTON_NORMAL, hover_color=BUTTON_HOVER)
        btn.update_hover(mouse_pos)
        
        # Custom draw for level buttons
        color = btn.hover_color if btn.hovered else btn.base_color
        rect = btn.rect
        
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=8)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, (255,255,255), rect, 2, border_radius=8)
        
        # Level name
        name_surf = medium_font.render(level['name'], True, ACCENT_COLOR)
        screen.blit(name_surf, (rect.x + 20, rect.y + 10))
        
        # Description
        desc_surf = tiny_font.render(level['description'], True, (200, 200, 200))
        screen.blit(desc_surf, (rect.x + 20, rect.y + 40))
        
        # Stars for completed levels - only show for last level
        if i == len(LEVELS) - 1 and level_stats[i].get('completed'):
            stars = level_stats[i].get('stars', 0)
            for j in range(3):
                star_color = (255, 215, 0) if j < stars else (80, 80, 80)
                pygame.draw.polygon(screen, star_color, get_star_points(rect.right - 100 + j * 30, rect.centery, 10))
        elif level_stats[i].get('completed'):
            # Just show a checkmark for completed non-final levels
            checkmark = medium_font.render('✓', True, (100, 255, 100))
            screen.blit(checkmark, (rect.right - 50, rect.centery - 15))
        
        level_buttons.append(btn)
    
    # Credit at bottom
    credit_text = tiny_font.render('Interactive Media class project by Youssif Goda for Prof. Russel McDermott', True, (150, 150, 150))
    screen.blit(credit_text, credit_text.get_rect(center=(WIDTH // 2, HEIGHT - 30)))
    
    return level_buttons

def draw_level_complete():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Completion box
    box_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150, 400, 300)
    pygame.draw.rect(screen, (40, 45, 55), box_rect, border_radius=15)
    pygame.draw.rect(screen, ACCENT_COLOR, box_rect, 3, border_radius=15)
    
    # Title
    title_surf = medium_font.render('Level Complete!', True, ACCENT_COLOR)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
    
    # Stats
    level = LEVELS[current_level]
    moves_surf = small_font.render(f'Moves: {move_count}', True, TEXT_COLOR)
    screen.blit(moves_surf, moves_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
    
    # Only show optimal comparison and stars for last level
    if current_level == len(LEVELS) - 1:
        optimal_surf = tiny_font.render(f'Optimal: {level["optimal_moves"]} moves', True, (200, 200, 200))
        screen.blit(optimal_surf, optimal_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        
        # Stars
        stars = get_star_rating(move_count, level['optimal_moves'])
        star_y = HEIGHT // 2 + 20
        for i in range(3):
            color = (255, 215, 0) if i < stars else (80, 80, 80)
            pygame.draw.polygon(screen, color, get_star_points(WIDTH // 2 - 50 + i * 50, star_y, 18))
    else:
        # For non-final levels, just show an encouraging message
        congrats_surf = tiny_font.render('Great job! Ready for the next challenge?', True, (150, 200, 255))
        screen.blit(congrats_surf, congrats_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))
    
    # Buttons
    mouse_pos = pygame.mouse.get_pos()
    
    if current_level < len(LEVELS) - 1:
        next_level_btn.update_hover(mouse_pos)
        next_level_btn.draw()
    else:
        # Game complete message
        complete_surf = small_font.render('All Levels Complete!', True, (100, 255, 100))
        screen.blit(complete_surf, complete_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
    
    menu_btn.update_hover(mouse_pos)
    menu_btn.draw()

def get_star_rating(moves, optimal):
    """Calculate star rating based on moves vs optimal - more forgiving thresholds"""
    if moves <= optimal:
        return 3
    elif moves <= optimal + 3:  # Within 3 moves of optimal
        return 2
    elif moves <= optimal + 6:  # Within 6 moves of optimal
        return 1
    return 0

def get_star_points(cx, cy, size):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = size if i % 2 == 0 else size // 2
        x = cx + radius * math.cos(angle)
        y = cy - radius * math.sin(angle)
        points.append((x, y))
    return points

def load_level(level_idx):
    global white_pieces, white_locations, black_locations, move_count, winner, selection, valid_moves, hint_piece, hint_move, current_level
    
    current_level = level_idx
    level = LEVELS[level_idx]
    
    white_pieces = level['white_pieces'].copy()
    white_locations = level['white_locations'].copy()
    black_locations = [level['black_start']]
    move_count = 0
    winner = ""
    selection = None
    valid_moves = []
    hint_piece = None
    hint_move = None

def reset_game():
    load_level(current_level)

# Movement check functions
def check_knight(position, white_locs, black_locs):
    moves = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
    res = []
    for dx, dy in moves:
        t = (position[0] + dx, position[1] + dy)
        if is_on_board(t) and t not in white_locs and t not in black_locs:
            res.append(t)
    return res

def check_rook(position, white_locs, black_locs):
    moves = []
    for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        for i in range(1, 6):
            target = (position[0] + direction[0] * i, position[1] + direction[1] * i)
            if not is_on_board(target) or target in white_locs or target in black_locs:
                break
            moves.append(target)
    return moves

def check_bishop(position, white_locs, black_locs):
    moves = []
    for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for i in range(1, 6):
            target = (position[0] + direction[0] * i, position[1] + direction[1] * i)
            if not is_on_board(target) or target in white_locs or target in black_locs:
                break
            moves.append(target)
    return moves

def check_options(piece, location, white_locs, black_locs):
    if piece == 'knight':
        return check_knight(location, white_locs, black_locs)
    elif piece == 'bishop':
        return check_bishop(location, white_locs, black_locs)
    elif piece == 'rook':
        return check_rook(location, white_locs, black_locs)
    return []

# BFS hint system
def find_empty_square(white_locs, black_locs):
    all_squares = []
    for y in range(3):
        for x in range(6):
            if y < 2 or (y == 2 and x >= 4):
                all_squares.append((x,y))
    occupied = set(white_locs) | set(black_locs)
    for sq in all_squares:
        if sq not in occupied:
            return sq
    return None

def get_moves_into_target(empty_pos, white_locs, black_locs):
    moves = []
    for idx, piece in enumerate(white_pieces):
        cur = white_locs[idx]
        opts = check_options(piece, cur, white_locs, black_locs)
        if empty_pos in opts:
            moves.append(('white', idx, cur, empty_pos))
    for idx, piece in enumerate(black_pieces):
        cur = black_locs[idx]
        opts = check_options(piece, cur, white_locs, black_locs)
        if empty_pos in opts:
            moves.append(('black', idx, cur, empty_pos))
    return moves

def bfs_find_next_move(white_locs, black_locs, target=(5,2), max_depth=20):
    start_empty = find_empty_square(white_locs, black_locs)
    if start_empty is None:
        return None

    start_state = (tuple(white_locs), tuple(black_locs))
    black_pos = black_locs[0]
    if target in check_knight(black_pos, white_locs, black_locs):
        return ('black', 0, target)

    queue = collections.deque()
    queue.append(start_state)
    parent = {start_state: None}
    found_state = None

    depth = {start_state: 0}
    while queue:
        state = queue.popleft()
        d = depth[state]
        w_locs = list(state[0])
        b_locs = list(state[1])
        empty = find_empty_square(w_locs, b_locs)
        if empty is None:
            continue

        if b_locs[0] == target:
            found_state = state
            break
        if d >= max_depth:
            continue

        moves = get_moves_into_target(empty, w_locs, b_locs)
        for mover in moves:
            mover_type, idx, cur_pos, dest = mover
            new_w = list(w_locs)
            new_b = list(b_locs)
            if mover_type == 'white':
                new_w[idx] = dest
            else:
                new_b[idx] = dest
            new_state = (tuple(new_w), tuple(new_b))
            if new_state not in parent:
                parent[new_state] = (state, mover)
                depth[new_state] = d + 1
                if new_b[0] == target:
                    found_state = new_state
                    queue.clear()
                    break
                queue.append(new_state)

    if not found_state:
        return None

    path_moves = []
    cur = found_state
    while parent[cur] is not None:
        prev_state, move = parent[cur]
        path_moves.append(move)
        cur = prev_state
    path_moves.reverse()
    if path_moves:
        first_move = path_moves[0]
        mover_type, idx, cur_pos, dest = first_move
        if mover_type == 'black':
            return ('black', idx, dest)
        else:
            return ('white', idx, dest)
    return None

# Animation helpers
def start_animation(piece_type, index, start_pos, end_pos, steps=12):
    global animating, anim_info
    animating = True
    anim_info = {
        'piece_type': piece_type,
        'index': index,
        'start': start_pos,
        'end': end_pos,
        'step': 0,
        'steps': steps
    }

def update_animation():
    global animating, anim_info, white_locations, black_locations, move_count, winner, selection, valid_moves, hint_piece, hint_move, game_state, level_stats
    if not animating or not anim_info:
        return
    anim_info['step'] += 1
    s = anim_info['start']
    e = anim_info['end']
    
    # easing function
    t = anim_info['step'] / anim_info['steps']
    t = t * t * (3 - 2 * t)  # smoothstep
    
    cur_x = s[0] + (e[0] - s[0]) * t
    cur_y = s[1] + (e[1] - s[1]) * t

    if anim_info['step'] >= anim_info['steps']:
        if anim_info['piece_type'] == 'white':
            white_locations[anim_info['index']] = anim_info['end']
        else:
            black_locations[anim_info['index']] = anim_info['end']
            target = LEVELS[current_level]['target']
            if black_locations[0] == target:
                move_count += 1
                winner = f"Level Complete!"
                game_state = 'level_complete'
                
                # Update level stats
                stars = get_star_rating(move_count, LEVELS[current_level]['optimal_moves'])
                if not level_stats[current_level].get('completed'):
                    level_stats[current_level]['completed'] = True
                    level_stats[current_level]['best_moves'] = move_count
                    level_stats[current_level]['stars'] = stars
                else:
                    if move_count < level_stats[current_level]['best_moves']:
                        level_stats[current_level]['best_moves'] = move_count
                        level_stats[current_level]['stars'] = max(stars, level_stats[current_level]['stars'])
                
                # Spawn celebration particles
                spawn_particles(5 * SQUARE_SIZE + 50, 2 * SQUARE_SIZE + 50, (255, 215, 0), 30)
        
        animating = False
        anim_info = None
        if winner == "":
            move_count += 1
        selection = None
        valid_moves = []
        hint_piece = None
        hint_move = None

def draw_anim_piece():
    if not animating or not anim_info:
        return
    s = anim_info['start']
    e = anim_info['end']
    t = anim_info['step'] / anim_info['steps']
    t = t * t * (3 - 2 * t)
    cur_x = s[0] + (e[0] - s[0]) * t
    cur_y = s[1] + (e[1] - s[1]) * t
    draw_x, draw_y = cur_x * SQUARE_SIZE + 10, cur_y * SQUARE_SIZE + 10
    if anim_info['piece_type'] == 'white':
        img = white_images[white_pieces[anim_info['index']]]
    else:
        img = black_images[black_pieces[anim_info['index']]]
    screen.blit(img, (draw_x, draw_y))

def main():
    global selection, valid_moves, move_count, winner, hint_piece, hint_move, animating, anim_info, game_state, particles

    # Start at menu
    game_state = 'menu'
    level_buttons = []

    run = True
    while run:
        timer.tick(fps)
        screen.fill(BACKGROUND_COLOR)
        
        # Update particles
        particles = [p for p in particles if p.update()]
        
        if game_state == 'menu':
            level_buttons = draw_menu()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, btn in enumerate(level_buttons):
                        if btn.clicked(event.pos):
                            load_level(i)
                            game_state = 'playing'
                            break
        
        elif game_state == 'playing':
            draw_board()
            draw_game_ui()
            draw_pieces()
            
            # Draw valid moves if selection
            if selection is not None and not animating and winner == "":
                if selection < len(white_pieces):
                    piece = white_pieces[selection]
                    loc = white_locations[selection]
                    valid_moves = check_options(piece, loc, white_locations, black_locations)
                else:
                    piece = black_pieces[0]
                    loc = black_locations[0]
                    valid_moves = check_options(piece, loc, white_locations, black_locations)
                draw_valid(valid_moves)
            
            # Draw hint arrow
            if hint_piece is not None and hint_move is not None:
                htype, hidx, hdest = hint_piece
                if htype == 'white':
                    cur = white_locations[hidx]
                    color = (0, 255, 0)
                else:
                    cur = black_locations[hidx]
                    color = (0, 0, 255)
                center = (cur[0]*SQUARE_SIZE + SQUARE_SIZE//2, cur[1]*SQUARE_SIZE + SQUARE_SIZE//2)
                new_center = (hdest[0]*SQUARE_SIZE + SQUARE_SIZE//2, hdest[1]*SQUARE_SIZE + SQUARE_SIZE//2)
                
                t = (pygame.time.get_ticks() % 1000) / 1000.0
                offset = math.sin(t * math.pi * 2) * 5
                pygame.draw.line(screen, (255, 255, 150), center, new_center, 4)
                pygame.draw.circle(screen, (255, 255, 150), new_center, 12 + int(offset))
                pygame.draw.circle(screen, (200, 200, 100), new_center, 10)
            
            # Handle animation
            if animating:
                update_animation()
                draw_anim_piece()
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if animating:
                        continue
                    mx, my = event.pos
                    
                    # Button handling
                    if play_again_btn.clicked(event.pos):
                        reset_game()
                        continue
                    if hint_btn.clicked(event.pos):
                        result = bfs_find_next_move(white_locations, black_locations, target=LEVELS[current_level]['target'])
                        if result:
                            hint_piece = result
                            hint_move = result[2]
                        else:
                            hint_piece = None
                            hint_move = None
                        continue
                    if exit_btn.clicked(event.pos):
                        game_state = 'menu'
                        continue
                    
                    # Board click
                    x_coord = mx // SQUARE_SIZE
                    y_coord = my // SQUARE_SIZE
                    click_coords = (x_coord, y_coord)
                    
                    if winner == "":
                        if click_coords in white_locations:
                            selection = white_locations.index(click_coords)
                            hint_piece = None
                            hint_move = None
                        elif click_coords in black_locations:
                            selection = black_locations.index(click_coords) + len(white_pieces)
                            hint_piece = None
                            hint_move = None
                        elif selection is not None:
                            if selection < len(white_pieces):
                                piece = white_pieces[selection]
                                loc = white_locations[selection]
                                valid_moves = check_options(piece, loc, white_locations, black_locations)
                            else:
                                piece = black_pieces[0]
                                loc = black_locations[0]
                                valid_moves = check_options(piece, loc, white_locations, black_locations)
                            if click_coords in valid_moves:
                                if selection < len(white_pieces):
                                    start_animation('white', selection, white_locations[selection], click_coords, steps=12)
                                else:
                                    start_animation('black', selection - len(white_pieces), black_locations[selection - len(white_pieces)], click_coords, steps=12)
                            else:
                                selection = None
                                valid_moves = []
                        else:
                            selection = None
                            valid_moves = []
        
        elif game_state == 'level_complete':
            draw_board()
            draw_pieces()
            draw_level_complete()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if current_level < len(LEVELS) - 1:
                        if next_level_btn.clicked(event.pos):
                            load_level(current_level + 1)
                            game_state = 'playing'
                    if menu_btn.clicked(event.pos):
                        game_state = 'menu'
        
        # Draw particles on top
        for p in particles:
            p.draw()
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()