import random
import tkinter as tk

from config import COLS, EMPTY, FALL_MS, FAST_FALL_MS, HYENA_CHANCE, ROWS, SCORE_BY_LINES, WINDOW_H, WINDOW_W
from drawing import TetricatDrawing
from input_controls import bind_user_inputs
from music import MidiMusic
from pieces import ALL_SHAPES, DOG_SHAPES, HYENA_KIND, Piece, SKULL_SHAPES, STANDARD_SHAPES


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
        self.hyena_notice = ""
        self.hyena_animation = None

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
        }
        self.mode_title = titles[mode]
        self.available_kinds = list(STANDARD_SHAPES)
        if mode in ("chaos", "skull", "hyena"):
            self.available_kinds += list(DOG_SHAPES)
        if mode in ("skull", "hyena"):
            self.available_kinds += list(SKULL_SHAPES)
        self.restart()

    def show_menu(self):
        self.mode = None
        self.current = None
        self.next_piece = None
        self.paused = False
        self.game_over = False
        self.soft_drop = False
        self.hyena_notice = ""
        self.hyena_animation = None
        self.draw()

    def handle_click(self, event):
        if self.mode is not None:
            return
        if 90 <= event.x <= 390 and 275 <= event.y <= 335:
            self.start_game("classic")
        elif 90 <= event.x <= 390 and 340 <= event.y <= 400:
            self.start_game("chaos")
        elif 90 <= event.x <= 390 and 405 <= event.y <= 465:
            self.start_game("skull")
        elif 90 <= event.x <= 390 and 470 <= event.y <= 530:
            self.start_game("hyena")

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
        if self.mode is None or self.current is None or self.hyena_animation or self.paused or self.game_over:
            return False
        if self.valid(self.current, dx=dx, dy=dy):
            self.current.x += dx
            self.current.y += dy
            self.draw()
            return True
        return False

    def rotate(self):
        if self.mode is None or self.current is None or self.hyena_animation or self.paused or self.game_over:
            return

        next_rotation = (self.current.rotation + 1) % len(ALL_SHAPES[self.current.kind])
        for kick in (0, -1, 1, -2, 2):
            if self.valid(self.current, dx=kick, rotation=next_rotation):
                self.current.x += kick
                self.current.rotation = next_rotation
                self.draw()
                return

    def hard_drop(self):
        if self.mode is None or self.current is None or self.hyena_animation or self.paused or self.game_over:
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
        self.hyena_notice = ""
        self.hyena_animation = None
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

        if self.mode == "hyena" and random.random() < HYENA_CHANCE:
            self.start_hyena_animation()
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
        self.hyena_notice = "Hyene en approche..."
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
            self.hyena_notice = f"Hyene: +1 en colonne {col + 1}"
            return

        self.game_over = True
        self.hyena_notice = "Hyene: colonne bouchee"

    def hyena_destroys_around(self, col, row):
        destroyed = 0
        for y in range(max(0, row - 1), min(ROWS, row + 2)):
            for x in range(max(0, col - 1), min(COLS, col + 2)):
                if abs(x - col) + abs(y - row) <= 1 and self.board[y][x] is not EMPTY:
                    self.board[y][x] = EMPTY
                    destroyed += 1
        self.hyena_notice = f"Hyene: {destroyed} case(s) grattee(s)"

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
        if self.mode is not None and self.current is not None and not self.hyena_animation and not self.paused and not self.game_over:
            if not self.move(0, 1):
                self.lock_piece()
        self.root.after(self.fall_delay(), self.tick)

    def run(self):
        self.root.mainloop()
