import random
import tkinter as tk

from config import (
    COLS,
    EMPTY,
    FALL_MS,
    FAST_FALL_MS,
    GHOST_CHANCE,
    GHOST_LIFETIME_PIECES,
    GHOST_SAFE_TOP_ROWS,
    HYENA_CHANCE,
    ROWS,
    SCORE_BY_LINES,
    WINDOW_H,
    WINDOW_W,
)
from drawing import TetricatDrawing
from input_controls import bind_user_inputs
from music import MidiMusic
from pieces import ALL_SHAPES, DOG_SHAPES, GHOST_KIND, HYENA_KIND, Piece, SKULL_SHAPES, STANDARD_SHAPES


class Tetricat(TetricatDrawing):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tetricat")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_W,
            height=WINDOW_H,
            bg="#151820",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.music = MidiMusic()
        self.music.play()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.mode = None
        self.mode_title = ""
        self.available_kinds = []
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.bag = []
        self.current = None
        self.next_piece = None
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self.soft_drop = False
        self.event_notice = ""
        self.hyena_animation = None
        self.ghost_animation = None
        self.ghost_blocks = []

        bind_user_inputs(self)

        self.draw()
        self.tick()

    def refill_bag(self):
        self.bag = list(self.available_kinds)
        random.shuffle(self.bag)

    def new_piece(self):
        if not self.bag:
            self.refill_bag()
        return Piece(self.bag.pop())

    def start_game(self, mode):
        self.mode = mode
        titles = {
            "classic": "Classique chats",
            "chaos": "Chaos chiens",
            "skull": "Tetes de mort",
            "hyena": "Hyene panique",
            "ghost": "Fantomes 2x2",
        }
        self.mode_title = titles[mode]
        self.available_kinds = list(STANDARD_SHAPES)
        if mode in ("chaos", "skull", "hyena", "ghost"):
            self.available_kinds += list(DOG_SHAPES)
        if mode in ("skull", "hyena", "ghost"):
            self.available_kinds += list(SKULL_SHAPES)
        self.restart()

    def show_menu(self):
        self.mode = None
        self.current = None
        self.next_piece = None
        self.paused = False
        self.game_over = False
        self.soft_drop = False
        self.event_notice = ""
        self.hyena_animation = None
        self.ghost_animation = None
        self.ghost_blocks = []
        self.draw()

    def handle_click(self, event):
        if self.mode is not None:
            return
        if 90 <= event.x <= 390 and 250 <= event.y <= 310:
            self.start_game("classic")
        elif 90 <= event.x <= 390 and 305 <= event.y <= 365:
            self.start_game("chaos")
        elif 90 <= event.x <= 390 and 360 <= event.y <= 420:
            self.start_game("skull")
        elif 90 <= event.x <= 390 and 415 <= event.y <= 475:
            self.start_game("hyena")
        elif 90 <= event.x <= 390 and 470 <= event.y <= 530:
            self.start_game("ghost")

    def valid(self, piece, dx=0, dy=0, rotation=None, x=None, y=None):
        test_x = piece.x + dx if x is None else x
        test_y = piece.y + dy if y is None else y
        for x, y in piece.cells(rotation=rotation, x=test_x, y=test_y):
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not EMPTY:
                return False
        return True

    def move(self, dx, dy):
        if self.mode is None or self.current is None or self.event_animation_active() or self.paused or self.game_over:
            return False
        if self.valid(self.current, dx=dx, dy=dy):
            self.current.x += dx
            self.current.y += dy
            self.draw()
            return True
        return False

    def rotate(self):
        if self.mode is None or self.current is None or self.event_animation_active() or self.paused or self.game_over:
            return

        next_rotation = (self.current.rotation + 1) % len(ALL_SHAPES[self.current.kind])
        for kick in (0, -1, 1, -2, 2):
            if self.valid(self.current, dx=kick, rotation=next_rotation):
                self.current.x += kick
                self.current.rotation = next_rotation
                self.draw()
                return

    def hard_drop(self):
        if self.mode is None or self.current is None or self.event_animation_active() or self.paused or self.game_over:
            return
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        self.lock_piece()

    def start_soft_drop(self, _):
        self.soft_drop = True

    def stop_soft_drop(self, _):
        self.soft_drop = False

    def toggle_pause(self):
        if self.game_over:
            return
        if self.mode is None:
            return
        self.paused = not self.paused
        self.draw()

    def toggle_music(self):
        self.music.toggle()
        self.draw()

    def close(self):
        self.music.close()
        self.root.destroy()

    def restart(self):
        if self.mode is None:
            self.show_menu()
            return
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.bag = []
        self.current = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self.soft_drop = False
        self.event_notice = ""
        self.hyena_animation = None
        self.ghost_animation = None
        self.ghost_blocks = []
        self.draw()

    def lock_piece(self):
        for x, y in self.current.cells():
            if y < 0:
                self.game_over = True
                self.draw()
                return
            self.board[y][x] = self.current.kind

        cleared = self.clear_lines()
        if cleared:
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.score += SCORE_BY_LINES.get(cleared, 1200 + (cleared - 4) * 500) * self.level

        self.sync_ghost_blocks_after_line_clear()
        ghost_exploded = self.age_ghost_blocks()
        if self.game_over:
            self.draw()
            return

        if self.mode == "hyena" and random.random() < HYENA_CHANCE:
            self.start_hyena_animation()
            return
        if self.mode == "ghost" and not ghost_exploded and not self.ghost_blocks and random.random() < GHOST_CHANCE:
            self.start_ghost_animation()
            return

        self.spawn_next_piece()

    def spawn_next_piece(self):
        self.current = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid(self.current):
            self.game_over = True
        self.draw()

    def start_hyena_animation(self):
        col = random.randrange(COLS)
        first_occupied = next((y for y in range(ROWS) if self.board[y][col] is not EMPTY), None)
        impact_y = ROWS - 1 if first_occupied is None else max(0, first_occupied - 1)
        action = "add" if random.random() < 0.5 else "destroy"

        self.current = None
        self.event_notice = "Hyene en approche..."
        self.hyena_animation = {
            "col": col,
            "row": -1.3,
            "target": impact_y,
            "action": action,
        }
        self.animate_hyena()

    def animate_hyena(self):
        if self.mode != "hyena" or self.hyena_animation is None:
            return

        target = self.hyena_animation["target"]
        if self.hyena_animation["row"] < target:
            self.hyena_animation["row"] = min(target, self.hyena_animation["row"] + 0.72)
            self.draw()
            self.root.after(42, self.animate_hyena)
            return

        col = self.hyena_animation["col"]
        action = self.hyena_animation["action"]
        self.hyena_animation = None

        if action == "add":
            self.hyena_adds_block(col, target)
        else:
            self.hyena_destroys_around(col, target)

        if self.game_over:
            self.draw()
            return
        self.spawn_next_piece()

    def hyena_adds_block(self, col, row):
        if self.board[row][col] is EMPTY:
            self.board[row][col] = HYENA_KIND
            self.event_notice = f"Hyene: +1 en colonne {col + 1}"
            return

        self.game_over = True
        self.event_notice = "Hyene: colonne bouchee"

    def hyena_destroys_around(self, col, row):
        destroyed = 0
        for y in range(max(0, row - 1), min(ROWS, row + 2)):
            for x in range(max(0, col - 1), min(COLS, col + 2)):
                if abs(x - col) + abs(y - row) <= 1 and self.board[y][x] is not EMPTY:
                    self.board[y][x] = EMPTY
                    destroyed += 1
        self.event_notice = f"Hyene: {destroyed} case(s) grattee(s)"

    def start_ghost_animation(self):
        col = random.randrange(0, COLS - 1)
        row = random.randrange(GHOST_SAFE_TOP_ROWS, ROWS - 1)
        self.current = None
        self.event_notice = "Fantomes en approche..."
        self.ghost_animation = {
            "col": col,
            "row": row,
            "progress": 0.0,
        }
        self.animate_ghosts()

    def animate_ghosts(self):
        if self.mode != "ghost" or self.ghost_animation is None:
            return

        if self.ghost_animation["progress"] < 1.0:
            self.ghost_animation["progress"] = min(1.0, self.ghost_animation["progress"] + 0.08)
            self.draw()
            self.root.after(46, self.animate_ghosts)
            return

        col = self.ghost_animation["col"]
        row = self.ghost_animation["row"]
        cells = [(col + dx, row + dy) for dy in range(2) for dx in range(2)]
        for x, y in cells:
            self.board[y][x] = GHOST_KIND
        self.ghost_blocks = [{"cells": cells, "pieces_left": GHOST_LIFETIME_PIECES}]
        self.ghost_animation = None
        self.event_notice = "Fantomes: 3 pieces avant explosion"
        self.spawn_next_piece()

    def age_ghost_blocks(self):
        if self.mode != "ghost" or not self.ghost_blocks:
            return False

        remaining_blocks = []
        exploded = False
        for block in self.ghost_blocks:
            block["pieces_left"] -= 1
            if block["pieces_left"] <= 0:
                self.explode_ghost_block(block)
                exploded = True
            else:
                remaining_blocks.append(block)
        self.ghost_blocks = remaining_blocks
        if self.ghost_blocks:
            pieces_left = min(block["pieces_left"] for block in self.ghost_blocks)
            self.event_notice = f"Fantomes: explosion dans {pieces_left} piece(s)"
        return exploded

    def sync_ghost_blocks_after_line_clear(self):
        if self.mode != "ghost" or not self.ghost_blocks:
            return

        ghost_cells = [
            (x, y)
            for y, row in enumerate(self.board)
            for x, kind in enumerate(row)
            if kind == GHOST_KIND
        ]
        if ghost_cells:
            self.ghost_blocks[0]["cells"] = ghost_cells
        else:
            self.ghost_blocks = []

    def explode_ghost_block(self, block):
        exploded = 0
        for x, y in block["cells"]:
            if 0 <= x < COLS and 0 <= y < ROWS and self.board[y][x] == GHOST_KIND:
                self.board[y][x] = EMPTY
                exploded += 1
        if exploded:
            self.music.play_explosion()
            self.event_notice = "Fantomes: BOUM"

    def clear_lines(self):
        kept = [row for row in self.board if any(cell is EMPTY for cell in row)]
        cleared = ROWS - len(kept)
        if cleared:
            self.board = [[EMPTY for _ in range(COLS)] for _ in range(cleared)] + kept
        return cleared

    def fall_delay(self):
        base = max(110, FALL_MS - (self.level - 1) * 42)
        return FAST_FALL_MS if self.soft_drop else base

    def tick(self):
        if self.mode is not None and self.current is not None and not self.event_animation_active() and not self.paused and not self.game_over:
            if not self.move(0, 1):
                self.lock_piece()
        self.root.after(self.fall_delay(), self.tick)

    def event_animation_active(self):
        return self.hyena_animation is not None or self.ghost_animation is not None

    def run(self):
        self.root.mainloop()
