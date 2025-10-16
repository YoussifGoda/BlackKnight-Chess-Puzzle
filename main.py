import pygame
import collections
import sys
import os
import math

pygame.init()
WIDTH = 900
HEIGHT = 600
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
    # Normalize path separators
    relative_path = os.path.normpath(relative_path)
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
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

timer = pygame.time.Clock()
fps = 60

# Game variables and images
white_pieces = ['bishop', 'bishop', 'bishop', 'bishop', 'rook', 'knight', 'knight', 'knight', 'knight', 'rook', 'rook', 'rook']
white_locations = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
                   (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (4, 2)]
black_pieces = ['knight']
black_locations = [(0, 0)]
selection = None
valid_moves = []
move_count = 0
winner = ""
game_history = []  # List to store previous game results

hint_piece = None
hint_move = None
hint_show_time = 0

# Animation state
animating = False
anim_info = None  # dict with: piece_type ('white'/'black'), index, start, end, step, steps

# UI state
ui_pulse = 0
button_feedback = {'play': 0, 'hint': 0}  # feedback timers

# Load and scale images with safe fallback
def load_image(path, size):
    """
    Path must be relative path in your project, e.g.:
      'build/web/assets/images/black knight.png'
    This helper uses resource_path() so the file is found in dev and in the PyInstaller exe.
    """
    try:
        full = resource_path(path)
        img = pygame.image.load(full).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        # create placeholder if loading fails
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((180, 180, 180, 255))
        pygame.draw.rect(surf, (100, 100, 100), surf.get_rect(), 3)
        return surf

# Use the same paths you used before; resource_path will resolve them under the exe
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
piece_list = ['knight', 'bishop', 'rook']

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
ACCENT_COLOR = (255, 200, 80)

BOARD_ORIGIN = (0, 0)
SQUARE_SIZE = 100

def is_on_board(position):
    x, y = position
    if y < 2:
        return 0 <= x <= 5
    elif y == 2:
        return 4 <= x <= 5
    return False

def draw_board():
    # board squares: rows 0..2; row2 only cols 4,5
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

def draw_pieces(anim_offset=(0,0)):
    # white pieces
    for i, (piece, loc) in enumerate(zip(white_pieces, white_locations)):
        img = white_images.get(piece, white_knight)
        draw_x, draw_y = loc[0] * SQUARE_SIZE + 10, loc[1] * SQUARE_SIZE + 10
        if animating and anim_info and anim_info['piece_type']=='white' and anim_info['index']==i:
            continue
        
        # hover effect
        if selection == i:
            # scale up slightly
            scaled = pygame.transform.smoothscale(img, (90, 90))
            screen.blit(scaled, (draw_x - 5, draw_y - 5))
        else:
            screen.blit(img, (draw_x, draw_y))
        
        # selection highlight
        if selection == i:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            t = pygame.time.get_ticks() / 300.0
            alpha = int(100 + 50 * math.sin(t))
            s.fill((255, 255, 0, alpha))
            screen.blit(s, (loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE))
            pygame.draw.rect(s, (255, 255, 100, 255), s.get_rect(), 2)
            screen.blit(s, (loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE))

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
            pygame.draw.rect(s, (255, 255, 100, 255), s.get_rect(), 2)
            screen.blit(s, (loc[0] * SQUARE_SIZE, loc[1] * SQUARE_SIZE))

def draw_valid(valid_moves):
    # pulsing indicator with enhanced visuals
    t = pygame.time.get_ticks() / 250.0
    radius = 20 + int(8 * (0.5 + 0.5 * math.sin(t)))
    for move in valid_moves:
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 200, 255, 180), (SQUARE_SIZE//2, SQUARE_SIZE//2), radius)
        pygame.draw.circle(s, (200, 255, 255, 200), (SQUARE_SIZE//2, SQUARE_SIZE//2), radius - 3, 2)
        screen.blit(s, (move[0] * SQUARE_SIZE, move[1] * SQUARE_SIZE))

class Button:
    def __init__(self, rect, text, base_color=BUTTON_NORMAL, hover_color=None, accent_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color if hover_color else (min(base_color[0]+30, 255), min(base_color[1]+30, 255), min(base_color[2]+30, 255))
        self.hovered = False
        self.pressed = False
        self.press_timer = 0
    
    def draw(self):
        color = self.hover_color if self.hovered else self.base_color
        
        # add press effect
        if self.pressed:
            self.press_timer -= 1
            press_amount = max(0, self.press_timer / 10.0)
            offset_y = int(press_amount * 3)
        else:
            offset_y = 0
        
        rect = self.rect.copy()
        rect.y += offset_y
        
        # shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=6)
        
        # button
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (255,255,255), rect, 2, border_radius=6)
        
        # text
        text_surf = small_font.render(self.text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
    
    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def clicked(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.pressed = True
            self.press_timer = 10
            return True
        return False

# Buttons
play_again_btn = Button((500, 520, 120, 50), "Play Again", base_color=BUTTON_DANGER, hover_color=BUTTON_DANGER_HOVER)
hint_btn = Button((350, 520, 120, 50), "Hint", base_color=BUTTON_ACCENT, hover_color=BUTTON_ACCENT_HOVER)
exit_btn = Button((650, 520, 120, 50), "Exit", base_color=BUTTON_EXIT, hover_color=BUTTON_EXIT_HOVER)

def draw_ui():
    global ui_pulse
    ui_pulse += 1
    
    # bottom panel with gradient effect
    pygame.draw.rect(screen, (25, 30, 40), [0, 300, WIDTH, 300])
    pygame.draw.line(screen, (100, 120, 160), (0, 300), (WIDTH, 300), 2)
    
    screen.blit(big_font.render('Black Knight', True, ACCENT_COLOR), (20, 230))
    screen.blit(small_font.render('Move the Black Knight to the light blue square! (No captures)', True, TEXT_COLOR), (20, 320))
    screen.blit(small_font.render('Click a piece, then click a highlighted square to move it.', True, (200, 200, 200)), (20, 345))
    screen.blit(small_font.render('This puzzle could be solved in 18 moves!', True, (200, 200, 200)), (20, 370))
    
    move_text = small_font.render(f'Moves: {move_count}', True, ACCENT_COLOR)
    screen.blit(move_text, (700, 20))
    
    # Display previous game history
    history_y = 55
    if game_history:
        screen.blit(tiny_font.render('Previous Attempts:', True, ACCENT_COLOR), (700, history_y))
        history_y += 25
        for i, entry in enumerate(game_history[-3:]):  # Show last 3 attempts
            status_color = (100, 255, 100) if entry['completed'] else (200, 100, 100)
            status_text = "Win" if entry['completed'] else "Did Not Finish"
            history_text = tiny_font.render(f"Try {entry['attempt']}: {entry['moves']} mvs - {status_text}", True, status_color)
            screen.blit(history_text, (700, history_y))
            history_y += 22

    # buttons
    mouse_pos = pygame.mouse.get_pos()
    play_again_btn.update_hover(mouse_pos)
    hint_btn.update_hover(mouse_pos)
    exit_btn.update_hover(mouse_pos)
    play_again_btn.draw()
    hint_btn.draw()
    exit_btn.draw()

def reset_game():
    global white_locations, black_locations, move_count, winner, selection, valid_moves, hint_piece, hint_move
    white_locations = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
                       (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (4, 2)]
    black_locations[:] = [(0, 0)]
    move_count = 0
    winner = ""
    selection = None
    valid_moves = []
    hint_piece = None
    hint_move = None

# Movement check functions (reuse from original but safer)
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

# --- BFS that only moves pieces INTO the single empty square ---
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
    global animating, anim_info, white_locations, black_locations, move_count, winner, selection, valid_moves, hint_piece, hint_move, game_history
    if not animating or not anim_info:
        return
    anim_info['step'] += 1
    s = anim_info['start']
    e = anim_info['end']
    
    # easing function for smoother animation
    t = anim_info['step'] / anim_info['steps']
    t = t * t * (3 - 2 * t)  # smoothstep
    
    cur_x = s[0] + (e[0] - s[0]) * t
    cur_y = s[1] + (e[1] - s[1]) * t

    if anim_info['step'] >= anim_info['steps']:
        if anim_info['piece_type'] == 'white':
            white_locations[anim_info['index']] = anim_info['end']
        else:
            black_locations[anim_info['index']] = anim_info['end']
            if black_locations[0] == (5,2):
                move_count += 1
                winner = f"Black Knight wins in {move_count} moves!"
                game_history.append({
                    'attempt': len(game_history) + 1,
                    'moves': move_count,
                    'completed': True
                })
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
    global selection, valid_moves, move_count, winner, hint_piece, hint_move, animating, anim_info, game_history

    run = True
    while run:
        timer.tick(fps)
        screen.fill(BACKGROUND_COLOR)
        draw_board()

        # UI
        draw_ui()

        # draw pieces (except animating one)
        draw_pieces()

        # draw valid moves if selection
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

        # draw hint arrow if present
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
            
            # animated arrow
            t = (pygame.time.get_ticks() % 1000) / 1000.0
            offset = math.sin(t * math.pi * 2) * 5
            pygame.draw.line(screen, (255, 255, 150), center, new_center, 4)
            pygame.draw.circle(screen, (255, 255, 150), new_center, 12 + int(offset))
            pygame.draw.circle(screen, (200, 200, 100), new_center, 10)

        # handle animation updates/draw on top
        if animating:
            update_animation()
            draw_anim_piece()

        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if animating:
                    continue
                mx, my = event.pos
                # buttons
                if play_again_btn.clicked(event.pos):
                    if move_count > 0 and winner == "":
                        game_history.append({
                            'attempt': len(game_history) + 1,
                            'moves': move_count,
                            'completed': False
                        })
                    reset_game()
                    continue
                if hint_btn.clicked(event.pos):
                    result = bfs_find_next_move(white_locations, black_locations, target=(5,2))
                    if result:
                        hint_piece = result
                        hint_move = result[2]
                    else:
                        hint_piece = None
                        hint_move = None
                    continue
                if exit_btn.clicked(event.pos):
                    run = False
                    continue

                # board click
                x_coord = mx // SQUARE_SIZE
                y_coord = my // SQUARE_SIZE
                click_coords = (x_coord, y_coord)

                # selection or move
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

        if winner:
            # fancy win screen
            win_text = big_font.render(winner, True, ACCENT_COLOR)
            t = pygame.time.get_ticks() / 300.0
            scale = 1 + 0.1 * math.sin(t)
            win_text = pygame.transform.smoothscale(win_text, (int(win_text.get_width() * scale), int(win_text.get_height() * scale)))
            win_rect = win_text.get_rect(center=(WIDTH // 2, 450))
            screen.blit(win_text, win_rect)

        # draw anim piece again if necessary
        if animating:
            draw_anim_piece()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()