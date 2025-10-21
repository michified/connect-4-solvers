import pygame as pg
import os
import sys
import random
import copy

pg.init()


class BoardState:
    def __init__(self, width=7, height=6):
        self.width = width
        self.height = height
        self.cmpBitBoard = 0
        self.hmnBitBoard = 0
        self.numPieces = [0] * width
        self.bitwiseDirs = [1, 7, 8, 6]
        self.board = [[None] * width for _ in range(height)]

    def addPieceCmp(self, col):
        if self.numPieces[col] == self.height:
            return False
        self.cmpBitBoard ^= 1 << (col * 7 + self.numPieces[col])
        self.numPieces[col] += 1
        return True

    def addPieceHmn(self, col):
        if self.numPieces[col] == self.height:
            return False
        self.hmnBitBoard ^= 1 << (col * 7 + self.numPieces[col])
        self.numPieces[col] += 1
        return True

    def isWin(self):
        for direction in self.bitwiseDirs:
            if (
                self.cmpBitBoard & (self.cmpBitBoard >> direction) &
                (self.cmpBitBoard >> (direction * 2)) &
                (self.cmpBitBoard >> (direction * 3))
            ) != 0:
                return 1
        for direction in self.bitwiseDirs:
            if (
                self.hmnBitBoard & (self.hmnBitBoard >> direction) &
                (self.hmnBitBoard >> (direction * 2)) &
                (self.hmnBitBoard >> (direction * 3))
            ) != 0:
                return -1
        return 0


class Button:
    def __init__(self, text, pos, size, action=None, frame=None, back=False, theme=None):
        self.text = text
        self.pos = pos
        self.size = size
        self.action = action
        self.rect = pg.Rect(pos, size)
        self.hovered = False
        self.frame = frame
        self.back = back
        self.theme = theme

    def draw(self):
        font = get_theme_font(22)
        shrink = 0.95 if self.hovered else 1.0
        draw_size = (int(self.size[0] * shrink), int(self.size[1] * shrink))
        draw_pos = (
            self.pos[0] + (self.size[0] - draw_size[0]) // 2,
            self.pos[1] + (self.size[1] - draw_size[1]) // 2
        )
        draw_rect = pg.Rect(draw_pos, draw_size)
        pg.draw.rect(screen, colorSchemes[currentTheme]["button"], draw_rect, border_radius=10)
        text_surface = font.render(self.text, True, colorSchemes[currentTheme]["text"])
        text_rect = text_surface.get_rect(center=draw_rect.center)
        screen.blit(text_surface, text_rect)

    def check_click(self, mouse_pos):
        global pending_frame_change, pending_frame_args
        if self.rect.collidepoint(mouse_pos):
            global transitionPos
            transitionPos = 0
            if self.action:
                self.action()
            if self.back:
                pending_frame_change = "__BACK__"
                pending_frame_args = {}
            elif self.theme is not None and self.frame is None:
                pending_frame_change = currentFrame
                pending_frame_args = {"theme": self.theme}
            elif self.frame:
                pending_frame_change = self.frame
                pending_frame_args = {"back": False, "theme": self.theme}

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)


class Slider(Button):
    def __init__(self, text, pos, size, min_value=0, max_value=100, initial_value=50):
        super().__init__(text, pos, size)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.slider_rect = pg.Rect(pos[0] + 10, pos[1] + size[1] // 2 - 5, size[0] - 20, 10)
        self.dragging = False

    def draw(self):
        font = get_theme_font(18)
        caption_surface = font.render(self.text, True, colorSchemes[currentTheme]["text"])
        caption_rect = caption_surface.get_rect(midbottom=(self.pos[0] + self.size[0] // 2, self.pos[1] - 5))
        screen.blit(caption_surface, caption_rect)
        pg.draw.rect(screen, colorSchemes[currentTheme]["frame"], self.slider_rect, border_radius=5)
        slider_pos = (self.value - self.min_value) / (self.max_value - self.min_value) * (self.size[0] - 20)
        knob_rect = pg.Rect(self.pos[0] + 10 + slider_pos - 8, self.pos[1] + self.size[1] // 2 - 12, 16, 24)
        pg.draw.rect(screen, colorSchemes[currentTheme]["button"], knob_rect, border_radius=8)
        value_surface = font.render(str(self.value), True, colorSchemes[currentTheme]["text"])
        value_rect = value_surface.get_rect(midleft=(self.pos[0] + self.size[0] + 10, self.pos[1] + self.size[1] // 2))
        screen.blit(value_surface, value_rect)
        if currentFrame == "selectdifficulty":
            font = get_theme_font(16)
            stage = ["Very Easy", "Easy", "Medium", "Hard", "Expert", "Maximum"][self.value // 20]
            stage_text = f"Difficulty: {stage}"
            stage_surface = font.render(stage_text, True, colorSchemes[currentTheme]["text"])
            screen.blit(stage_surface, (self.pos[0], self.pos[1] + self.size[1] + 5))

    def check_click(self, mouse_pos):
        if self.slider_rect.collidepoint(mouse_pos):
            self.dragging = True
            self.update_value(mouse_pos)
            if self.action:
                self.action()
        elif self.rect.collidepoint(mouse_pos):
            self.update_value(mouse_pos)
            if self.action:
                self.action()

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION and self.dragging:
            self.update_value(event.pos)
            if self.action:
                self.action()

    def update_value(self, mouse_pos):
        relative_x = mouse_pos[0] - (self.pos[0] + 10)
        self.value = int(relative_x / (self.size[0] - 20) * (self.max_value - self.min_value)) + self.min_value
        if self.value < self.min_value:
            self.value = self.min_value
        elif self.value > self.max_value:
            self.value = self.max_value

# --- Constants and Globals ---
SQUARESIZE = 100
width = 7
height = 6
WINDOWWIDTH = SQUARESIZE * width
WINDOWHEIGHT = SQUARESIZE * (height + 2)
CIRCLERADIUS = SQUARESIZE / 2 - 10
windowsize = (WINDOWWIDTH, WINDOWHEIGHT)
screen = pg.display.set_mode(windowsize)
transitionPos = -1

BLUE = (0, 0, 200)
YELLOW = (200, 200, 0)
TRANSPARENTYELLOW = (59, 59, 2)
RED = (200, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

themeLibrary = {
    "bubblegum": (255, 105, 180),
    "mint": (152, 255, 152),
    "greyscale": (128, 128, 128),
    "coffee": (255, 204, 153),
    "sleek": (0, 0, 0),
    "magic": (255, 0, 255),
    "jungle": (0, 128, 0),
    "default": (0, 0, 200)
}

colorSchemes = {
    "bubblegum": {
        "frame": (80, 0, 60),
        "button": (180, 80, 140),
        "text": (255, 182, 193),
        "background": (10, 0, 15)
    },
    "mint": {
        "frame": (0, 60, 40),
        "button": (0, 120, 80),
        "text": (144, 238, 144),
        "background": (0, 10, 5)
    },
    "greyscale": {
        "frame": (40, 40, 40),
        "button": (80, 80, 80),
        "text": (220, 220, 220),
        "background": (5, 5, 5)
    },
    "coffee": {
        "frame": (60, 40, 0),
        "button": (120, 80, 20),
        "text": (255, 204, 153),
        "background": (10, 5, 0)
    },
    "sleek": {
        "frame": (10, 10, 20),
        "button": (40, 40, 60),
        "text": (220, 220, 255),
        "background": (0, 0, 0)
    },
    "magic": {
        "frame": (40, 0, 60),
        "button": (100, 0, 120),
        "text": (255, 200, 255),
        "background": (8, 0, 12)
    },
    "jungle": {
        "frame": (0, 40, 0),
        "button": (0, 80, 0),
        "text": (152, 251, 152),
        "background": (0, 8, 0)
    },
    "default": {
        "frame": (0, 0, 60),
        "button": (40, 40, 120),
        "text": (200, 200, 255),
        "background": (0, 0, 8)
    }
}

fonts = {
    "bubblegum": "jokerman",
    "mint": "gillsans",
    "greyscale": "consolas",
    "coffee": "bookantiqua",
    "sleek": "segoe ui",
    "magic": "papyrus",
    "jungle": "chiller",
    "default": "arial rounded"
}

currentTheme = "default"
currentFrame = "menu"
prevGameType = None
prevFrame = []
pending_frame_change = None
pending_frame_args = {}
frame_changed_this_transition = False
rematch_pending = False

# --- Utility Functions ---
def get_theme_font(size=24):
    font_name = fonts.get(currentTheme, "monospace")
    try:
        return pg.font.SysFont(font_name, size)
    except:
        return pg.font.SysFont("monospace", size)

def change_frame(frame=None, back=False, theme=None):
    global currentFrame, prevFrame, currentTheme
    if theme is not None and theme in themeLibrary:
        currentTheme = theme
    elif back:
        if prevFrame:
            currentFrame = prevFrame[-1]
            prevFrame.pop()
    elif frame is not None and frame in frames:
        prevFrame.append(currentFrame)
        currentFrame = frame
    else:
        if frame is not None:
            print(f"Frame '{frame}' does not exist.")
        if theme is not None and theme not in themeLibrary:
            print(f"Theme '{theme}' does not exist.")

def reset_scores():
    global player1_score, player2_score
    player1_score = 0
    player2_score = 0

def set_first_player(player):
    global first_player
    first_player = player

def set_allowedMS(ms):
    global allowedMS
    allowedMS = ms

def set_difficulty_slider(val):
    global allowedMS, randomness
    if val < 75:
        randomness = int(100 - (val / 75) * 100)
        allowedMS = 1
    else:
        randomness = 0
        t = (val - 75) / 25
        allowedMS = int(10 * (1000 ** t))

def rematch():
    # Schedule a rematch so the transition animation runs, the frame changes during the transition,
    # and the board/state reset happens when the frame is applied.
    global pending_frame_change, pending_frame_args, rematch_pending, prevGameType
    target = prevGameType if prevGameType else "menu"
    pending_frame_change = target
    pending_frame_args = {"back": False, "theme": None}
    rematch_pending = True

# --- Drawing Functions ---
def render_screen(board=None, animating_piece=None, current_col=None, player_turn=None, is_computer_game=False):
    global currentFrame, transitionPos
    screen.fill(colorSchemes[currentTheme]["background"])
    if currentFrame in ["gamebot", "gamehmn"]:
        top_offset = SQUARESIZE if currentFrame not in ["gamebot", "gamehmn"] else 2 * SQUARESIZE
        # Draw board background
        bg_surface = pg.Surface((WINDOWWIDTH, WINDOWHEIGHT - top_offset))
        bg_surface.fill(colorSchemes[currentTheme]["background"])
        player1_color = colorSchemes[currentTheme]["text"]
        player2_color = colorSchemes[currentTheme]["button"]
        if board:
            for row in range(board.height):
                for col in range(board.width):
                    cell = 1 << (col * 7 + row)
                    x = col * SQUARESIZE + SQUARESIZE // 2
                    y = (WINDOWHEIGHT - top_offset) - (row + 1) * SQUARESIZE + SQUARESIZE // 2
                    if board.cmpBitBoard & cell:
                        pg.draw.circle(bg_surface, player2_color, (x, y), CIRCLERADIUS)
                    elif board.hmnBitBoard & cell:
                        pg.draw.circle(bg_surface, player1_color, (x, y), CIRCLERADIUS)
        if animating_piece:
            if isinstance(animating_piece, tuple) and len(animating_piece) == 3:
                x, y, color = animating_piece
                adjusted_y = y - top_offset if y >= top_offset else 0
                if adjusted_y >= 0:
                    pg.draw.circle(bg_surface, color, (x, adjusted_y), CIRCLERADIUS)
                    
        frame_surface = pg.Surface((WINDOWWIDTH, WINDOWHEIGHT - top_offset), pg.SRCALPHA)
        frame_surface.fill((*colorSchemes[currentTheme]["frame"], 255))
        for row in range(height):
            for col in range(width):
                x = col * SQUARESIZE + SQUARESIZE // 2
                y = (WINDOWHEIGHT - top_offset) - (row + 1) * SQUARESIZE + SQUARESIZE // 2
                pg.draw.circle(frame_surface, (0, 0, 0, 0), (x, y), CIRCLERADIUS)
        screen.blit(bg_surface, (0, top_offset))
        screen.blit(frame_surface, (0, top_offset))
        pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (0, 0, WINDOWWIDTH, top_offset))
        # Draw the arrow indicating the hovered column
        if current_col is not None:
            curCenter = current_col * SQUARESIZE + SQUARESIZE // 2
            arrow_color = player2_color if (is_computer_game or (player_turn == 1)) else player1_color
            arrow_y = SQUARESIZE + SQUARESIZE // 2  # Arrow base y position above the board
            pg.draw.polygon(
                screen,
                arrow_color,
                [
                    (curCenter, arrow_y + SQUARESIZE // 4),
                    (curCenter - SQUARESIZE // 4, arrow_y - SQUARESIZE // 4),
                    (curCenter, arrow_y - SQUARESIZE // 6),
                    (curCenter + SQUARESIZE // 4, arrow_y - SQUARESIZE // 4)
                ]
            )

        for button in frames[currentFrame]["buttons"]:
            button.draw()
        font = get_theme_font(28)
        score_text = f"Player 1: {player1_score}    Player 2: {player2_score}"
        text_surface = font.render(score_text, True, colorSchemes[currentTheme]["text"])
        screen.blit(text_surface, (WINDOWWIDTH // 2 - text_surface.get_width() // 2, 110))
    else:
        frame = frames[currentFrame]
        if "text" in frame:
            font = get_theme_font(26)
            text = frame["text"]
            lines = []
            for paragraph in text.split("\n"):
                words = paragraph.split(" ")
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if font.size(test_line)[0] > WINDOWWIDTH - 100:
                        lines.append(line)
                        line = word + " "
                    else:
                        line = test_line
                lines.append(line)
            y = 50
            for line in lines:
                text_surface = font.render(line.strip(), True, colorSchemes[currentTheme]["text"])
                screen.blit(text_surface, (50, y))
                y += font.get_linesize() + 10
        for button in frame["buttons"]:
            button.draw()
    pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (transitionPos - WINDOWWIDTH, 0, transitionPos, WINDOWHEIGHT))
    pg.display.flip()


def show_computer_thinking_strip(screen, board):
    top_offset = SQUARESIZE if currentFrame not in ["gamebot", "gamehmn"] else 2 * SQUARESIZE
    player1_color = colorSchemes[currentTheme]["text"]
    player2_color = colorSchemes[currentTheme]["button"]
    for row in range(board.height):
        for col in range(board.width):
            cell = 1 << (col * 7 + row)
            x = col * SQUARESIZE + SQUARESIZE // 2
            y = (WINDOWHEIGHT - top_offset) - (row + 1) * SQUARESIZE + SQUARESIZE // 2 + 2 * SQUARESIZE
            if board.cmpBitBoard & cell:
                pg.draw.circle(screen, player2_color, (x, y), CIRCLERADIUS)
            elif board.hmnBitBoard & cell:
                pg.draw.circle(screen, player1_color, (x, y), CIRCLERADIUS)
    strip_height = 80
    strip_rect = pg.Rect(0, screen.get_height() - strip_height, screen.get_width(), strip_height)
    pg.draw.rect(screen, colorSchemes[currentTheme]["background"], strip_rect)
    font = pg.font.SysFont(fonts[currentTheme], 36)
    msg = font.render("Computer is thinking...", True, colorSchemes[currentTheme]["text"])
    msg_rect = msg.get_rect(center=(screen.get_width() // 2, screen.get_height() - strip_height // 2))
    screen.blit(msg, msg_rect)
    pg.display.flip()


# --- Animation and Transition Functions ---
def animate_drop(board: BoardState, col: int, is_computer: bool, screen, player_turn=0, grace_ref=None):
    if board.numPieces[col] >= board.height:
        return False
    if grace_ref is not None:
        grace_ref[0] = 9999
    target_row = board.numPieces[col]
    current_y = 0
    velocity = 0
    gravity = 0.8
    damping = 0.6
    bounce_threshold = 2.0
    bounces_remaining = 2
    player1_color = colorSchemes[currentTheme]["text"]
    player2_color = colorSchemes[currentTheme]["button"]
    piece_color = player2_color if is_computer else player1_color
    x = col * SQUARESIZE + SQUARESIZE // 2
    while current_y < WINDOWHEIGHT - ((target_row + 1) * SQUARESIZE) or abs(velocity) > 0.1:
        render_screen(board, (x, current_y + SQUARESIZE // 2, piece_color), col, player_turn, is_computer_game=(currentFrame == "gamebot"))
        velocity += gravity
        current_y += velocity
        if current_y > WINDOWHEIGHT - ((target_row + 1) * SQUARESIZE):
            current_y = WINDOWHEIGHT - ((target_row + 1) * SQUARESIZE)
            if abs(velocity) > bounce_threshold and bounces_remaining > 0:
                velocity = -velocity * damping
                bounces_remaining -= 1
            else:
                velocity = 0
        pg.time.wait(5)
    if is_computer:
        board.cmpBitBoard ^= 1 << (col * 7 + target_row)
    else:
        board.hmnBitBoard ^= 1 << (col * 7 + target_row)
    board.numPieces[col] += 1
    # Draw the final piece as animating_piece for one frame to avoid disappearance
    render_screen(board, (x, WINDOWHEIGHT - ((target_row + 1) * SQUARESIZE) + SQUARESIZE // 2, piece_color), col, player_turn, is_computer_game=(currentFrame == "gamebot"))
    pg.time.wait(10)
    render_screen(board, None, col, player_turn, is_computer_game=(currentFrame == "gamebot"))
    if grace_ref is not None:
        grace_ref[0] = 10
    return True


# --- Game State and Frame Definitions ---
player1_score = 0
player2_score = 0
first_player = None
allowedMS = 0
randomness = 100

def setPrevGame(type):
    global prevGameType
    prevGameType = type

frames = {
    "menu": {
        "text": "Welcome to Connect Four!\nChoose an option below to start playing.",
        "buttons": [
            Button("Start Game", (50, 200), (250, 60), action=None, frame="choosegamemode"),
            Button("Settings", (50, 270), (250, 60), action=None, frame="settings"),
            Button("Reset Score", (50, 340), (250, 60), action=reset_scores, frame="menu"),
            Button("How to Play", (50, 410), (250, 60), action=None, frame="howtoplay"),
            Button("Exit", (50, 480), (250, 60), action=None, frame="quitscreen")
        ]
    },
    "choosegamemode": {
        "text": "How many players?",
        "buttons": [
            Button("1 Player", (50, 150), (250, 60), action=setPrevGame("gamebot"), frame="choosefirst_single"),
            Button("2 Players", (50, 220), (250, 60), action=setPrevGame("gamehmn"), frame="choosefirst_multi"),
            Button("Back", (50, 290), (200, 50), action=None, back=True)
        ]
    },
    "choosefirst_single": {
        "text": "Who goes first?",
        "buttons": [
            Button("Player", (50, 150), (200, 50), action=lambda: set_first_player('player'), frame="selectdifficulty"),
            Button("Computer", (270, 150), (200, 50), action=lambda: set_first_player('computer'), frame="selectdifficulty"),
            Button("Back", (50, 220), (200, 50), action=None, back=True)
        ]
    },
    "selectdifficulty": {
        "text": "Adjust Difficulty:",
        "buttons": [
            Slider("Difficulty", (50, 120), (350, 50), min_value=0, max_value=100, initial_value=0),
            Button("Start", (50, 200), (250, 60), action=None, frame="gamebot"),
            Button("Back", (320, 200), (120, 60), action=None, back=True)
        ]
    },
    "choosefirst_multi": {
        "text": "Who goes first?",
        "buttons": [
            Button("Player 1", (50, 150), (200, 50), action=lambda: set_first_player('player1'), frame="gamehmn"),
            Button("Player 2", (270, 150), (200, 50), action=lambda: set_first_player('player2'), frame="gamehmn"),
            Button("Back", (50, 220), (200, 50), action=None, back=True)
        ]
    },
    "gamebot": {
        "buttons": [
            Button("Exit Game", (WINDOWWIDTH // 2 - 120, 30), (240, 60), action=None, frame="forfeit")
        ]
    },
    "gamehmn": {
        "buttons": [
            Button("Exit Game", (WINDOWWIDTH // 2 - 120, 30), (240, 60), action=None, frame="forfeit")
        ]
    },
    "endscreen": {
        "buttons": [
            Button("Play Again", (50, 150), (250, 60), action=rematch, frame=None),
            Button("Main Menu", (50, 230), (250, 60), action=None, frame="menu"),
            Button("Reset Score", (50, 310), (250, 60), action=reset_scores, frame="endscreen"),
            Button("Exit", (50, 390), (250, 60), action=None, frame="quitscreen")
        ]
    },
    "howtoplay": {
        "text": "How to Play:\n1. Choose a column to drop your piece.\n2. Connect four pieces in a row, column, or diagonal to win.\n3. Take turns with your opponent.\n4. The game ends when one player wins or the board is full.",
        "buttons": [
            Button("Back", (50, 370), (200, 50), action=None, back=True)
        ]
    },
    "quitscreen": {
        "text": "Are you sure you want to exit the game?",
        "buttons": [
            Button("Yes, Exit", (50, 150), (200, 60), action=lambda: sys.exit()),
            Button("No, Go Back", (270, 150), (200, 60), action=None, back=True)
        ]
    },
    "forfeit": {
        "text": "Are you sure you want to forfeit the match and go back to the main menu?",
        "buttons": [
            Button("Yes, forfeit and return", (50, 180), (320, 60), action=None, frame="menu"),
            Button("No, continue game", (50, 260), (320, 60), action=None, back=True)
        ]
    },
    "settings": {
        "text": "Change your theme!",
        "buttons": [
            Button("Bubblegum", (50, 120), (200, 50), action=None, theme="bubblegum"),
            Button("Mint", (270, 120), (200, 50), action=None, theme="mint"),
            Button("Greyscale", (50, 190), (200, 50), action=None, theme="greyscale"),
            Button("Coffee", (270, 190), (200, 50), action=None, theme="coffee"),
            Button("Sleek", (50, 260), (200, 50), action=None, theme="sleek"),
            Button("Magic", (270, 260), (200, 50), action=None, theme="magic"),
            Button("Jungle", (50, 330), (200, 50), action=None, theme="jungle"),
            Button("Default", (270, 330), (200, 50), action=None, theme="default"),
            Button("Back", (50, 400), (200, 50), action=None, frame="menu")
        ]
    },
}

for btn in frames["selectdifficulty"]["buttons"]:
    if isinstance(btn, Slider):
        btn.action = lambda b=btn: set_difficulty_slider(b.value)

font = pg.font.SysFont("monospace", 30)
gameOver = False
last_column = -1
need_redraw = True
player_turn = 0
board = BoardState()
placed = 0
game_started = False
grace = [0]
prev_frame = None

while not gameOver:
    if transitionPos >= 0:
        transitionPos += 20
        pg.time.Clock().tick(240)
        if transitionPos >= 2 * WINDOWWIDTH:
            transitionPos = -1
            frame_changed_this_transition = False
        render_screen(board)

    if currentFrame == "menu" and prev_frame == "forfeit":
        board = BoardState()
        placed = 0
        last_column = -1
        player_turn = 0
        game_started = False
        need_redraw = True
    prev_frame = currentFrame

    if currentFrame == "gamebot":
        if not game_started:
            if first_player == 'computer':
                col = 3
                if animate_drop(board, col, True, screen, player_turn=1, grace_ref=[grace]):
                    placed += 1
            game_started = True
        if need_redraw:
            render_screen(board)
            need_redraw = False
        for event in pg.event.get():
            if grace[0] > 0:
                continue
            if event.type == pg.MOUSEMOTION:
                curCol = event.pos[0] // SQUARESIZE
                if curCol != last_column and 0 <= curCol < width:
                    render_screen(board, None, curCol, 0)
                    last_column = curCol
            if event.type == pg.QUIT:
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                for button in frames[currentFrame]["buttons"]:
                    if button.rect.collidepoint(mouse_pos):
                        button.check_click(mouse_pos)
                        break
                else:
                    col = mouse_pos[0] // SQUARESIZE
                    if animate_drop(board, col, False, screen, player_turn=0, grace_ref=grace):
                        placed += 1
                        if board.isWin() or placed == width * height:
                            winner = board.isWin()
                            strip_height = 80
                            strip_rect = pg.Rect(0, WINDOWHEIGHT // 2 - strip_height // 2, WINDOWWIDTH, strip_height)
                            pg.draw.rect(screen, (0,0,0), strip_rect)
                            winner_color = colorSchemes[currentTheme]["text"] if currentTheme != "greyscale" else WHITE
                            if winner == 1:
                                label = font.render("You Lost...", True, winner_color)
                                player2_score += 1
                            elif winner == -1:
                                label = font.render("You win!", True, winner_color)
                                player1_score += 1
                            else:
                                label = font.render("Tie!", True, winner_color)
                            score_rect = pg.Rect(WINDOWWIDTH // 2 - 200, 110, 400, 40)
                            pg.draw.rect(screen, colorSchemes[currentTheme]["background"], score_rect)
                            label_rect = label.get_rect(center=(WINDOWWIDTH // 2, WINDOWHEIGHT // 2))
                            screen.blit(label, label_rect)
                            pg.display.flip()
                            pg.time.wait(3000)
                            for i in range(WINDOWWIDTH):
                                pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                pg.display.flip()
                            currentFrame = "endscreen"
                            board = BoardState()
                            for i in range(WINDOWWIDTH, 2 * WINDOWWIDTH, 5):
                                render_screen()
                                pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                pg.display.flip()
                            placed = 0
                            break
                        render_screen()
                        show_computer_thinking_strip(screen, board)
                        pg.display.update()
                        cmp_col = None
                        pred = os.system(f"montecarlo.exe {board.cmpBitBoard} {board.hmnBitBoard} {500}")
                        board_copy = copy.deepcopy(board)
                        board_copy.addPieceCmp(pred)
                        board_copy2 = copy.deepcopy(board)
                        board_copy2.addPieceHmn(pred)
                        if board_copy.isWin() != 0 or board_copy2.isWin() != 0:
                            cmp_col = pred
                        else:
                            if randomness > 0 and random.randint(1, 100) <= randomness:
                                valid_cols = [c for c in range(width) if board.numPieces[c] < board.height]
                                cmp_col = random.choice(valid_cols)
                            else:
                                cmp_col = os.system(f"montecarlo.exe {board.cmpBitBoard} {board.hmnBitBoard} {allowedMS}")
                        if animate_drop(board, cmp_col, True, screen, player_turn=1):
                            placed += 1
                            grace[0] = 10
                            if board.isWin() or placed == width * height:
                                winner = board.isWin()
                                strip_height = 80
                                strip_rect = pg.Rect(0, WINDOWHEIGHT // 2 - strip_height // 2, WINDOWWIDTH, strip_height)
                                pg.draw.rect(screen, (0,0,0), strip_rect)
                                winner_color = colorSchemes[currentTheme]["text"] if currentTheme != "greyscale" else WHITE
                                if winner == 1:
                                    label = font.render("You Lost...", True, winner_color)
                                    player2_score += 1
                                elif winner == -1:
                                    label = font.render("You win!", True, winner_color)
                                    player1_score += 1
                                else:
                                    label = font.render("Tie!", True, winner_color)
                                score_rect = pg.Rect(WINDOWWIDTH // 2 - 200, 110, 400, 40)
                                pg.draw.rect(screen, colorSchemes[currentTheme]["background"], score_rect)
                                label_rect = label.get_rect(center=(WINDOWWIDTH // 2, WINDOWHEIGHT // 2))
                                screen.blit(label, label_rect)
                                pg.display.flip()
                                pg.time.wait(3000)
                                for i in range(WINDOWWIDTH):
                                    pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                    pg.display.flip()
                                currentFrame = "endscreen"
                                board = BoardState()
                                for i in range(WINDOWWIDTH, 2 * WINDOWWIDTH, 5):
                                    render_screen()
                                    pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                    pg.display.flip()
                                placed = 0
                                break
        if grace[0] > 0:
            grace[0] -= 1

    elif currentFrame == "gamehmn":
        if not game_started:
            player_turn = 0 if first_player == 'player1' else 1
            game_started = True
        if need_redraw:
            render_screen(board)
            need_redraw = False
        for event in pg.event.get():
            if grace[0] > 0:
                continue
            if event.type == pg.MOUSEMOTION:
                curCol = event.pos[0] // SQUARESIZE
                if curCol != last_column and 0 <= curCol < width:
                    render_screen(board, None, curCol, player_turn, False)
                    last_column = curCol
            if event.type == pg.QUIT:
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                for button in frames[currentFrame]["buttons"]:
                    if button.rect.collidepoint(mouse_pos):
                        button.check_click(mouse_pos)
                        break
                else:
                    col = mouse_pos[0] // SQUARESIZE
                    if animate_drop(board, col, player_turn == 1, screen, player_turn, grace_ref=grace):
                        placed += 1
                        if board.isWin() or placed == width * height:
                            winner = board.isWin()
                            strip_height = 80
                            strip_rect = pg.Rect(0, WINDOWHEIGHT // 2 - strip_height // 2, WINDOWWIDTH, strip_height)
                            pg.draw.rect(screen, (0,0,0), strip_rect)
                            winner_color = colorSchemes[currentTheme]["text"] if currentTheme != "greyscale" else WHITE
                            if winner == 1:
                                label = font.render("Player 2 Wins!", True, winner_color)
                                player2_score += 1
                            elif winner == -1:
                                label = font.render("Player 1 Wins!", True, winner_color)
                                player1_score += 1
                            else:
                                label = font.render("Tie!", True, winner_color)
                            score_rect = pg.Rect(WINDOWWIDTH // 2 - 200, 110, 400, 40)
                            pg.draw.rect(screen, colorSchemes[currentTheme]["background"], score_rect)
                            label_rect = label.get_rect(center=(WINDOWWIDTH // 2, WINDOWHEIGHT // 2))
                            screen.blit(label, label_rect)
                            pg.display.flip()
                            pg.time.wait(3000)
                            for i in range(0, WINDOWWIDTH, 1):
                                pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                pg.display.flip()
                            currentFrame = "endscreen"
                            board = BoardState()
                            for i in range(WINDOWWIDTH, 2 * WINDOWWIDTH, 5):
                                render_screen()
                                pg.draw.rect(screen, colorSchemes[currentTheme]["background"], (i - WINDOWWIDTH, 0, i, WINDOWHEIGHT))
                                pg.display.flip()
                            placed = 0
                            break
                        player_turn = 1 - player_turn
        if grace[0] > 0:
            grace[0] -= 1
    else:
        render_screen()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                for button in frames[currentFrame]["buttons"]:
                    button.check_click(mouse_pos)
            elif event.type in (pg.MOUSEBUTTONUP, pg.MOUSEMOTION):
                for button in frames[currentFrame]["buttons"]:
                    if isinstance(button, Slider):
                        button.handle_event(event)
    mouse_pos = pg.mouse.get_pos()
    for button in frames.get(currentFrame, {}).get("buttons", []):
        if hasattr(button, "update_hover"):
            button.update_hover(mouse_pos)
    if (
        pending_frame_change is not None and
        transitionPos >= WINDOWWIDTH and transitionPos < 2 * WINDOWWIDTH and
        not frame_changed_this_transition
    ):
        if pending_frame_change == "__BACK__":
            change_frame(back=True)
        else:
            change_frame(pending_frame_change, **pending_frame_args)
        # If a rematch was scheduled, reset the game state now that the frame has been changed
        if rematch_pending:
            # reset board and counters
            board = BoardState()
            placed = 0
            last_column = -1
            need_redraw = True
            grace = [0]
            game_started = False
            rematch_pending = False
        frame_changed_this_transition = True