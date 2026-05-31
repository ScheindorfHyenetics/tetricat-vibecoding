import tkinter as tk

from config import BOARD_H, BOARD_W, CELL, COLS, EMPTY, ROWS, WINDOW_H, WINDOW_W
from pieces import ALL_COLORS, ALL_SHAPES, DOG_KINDS, HYENA_KIND, SKULL_KINDS


class TetricatDrawing:
    def draw(self):
        self.canvas.delete("all")
        if self.mode is None:
            self.draw_title_screen()
            return
        self.draw_board_background()
        self.draw_landed_pieces()
        if self.current is not None:
            self.draw_ghost()
            self.draw_current_piece()
        self.draw_hyena_animation()
        self.draw_sidebar()

        if self.paused:
            self.draw_banner("PAUSE", "P pour reprendre")
        elif self.game_over:
            self.draw_banner("MIAOU TERMINAL", "R pour recommencer")

    def draw_board_background(self):
        self.canvas.create_rectangle(0, 0, BOARD_W, BOARD_H, fill="#1e2330", outline="")
        for x in range(COLS + 1):
            px = x * CELL
            self.canvas.create_line(px, 0, px, BOARD_H, fill="#2b3140")
        for y in range(ROWS + 1):
            py = y * CELL
            self.canvas.create_line(0, py, BOARD_W, py, fill="#2b3140")

    def draw_landed_pieces(self):
        for y, row in enumerate(self.board):
            for x, kind in enumerate(row):
                if kind is not EMPTY:
                    self.draw_piece_cell(x, y, kind)

    def draw_current_piece(self):
        for x, y in self.current.cells():
            if y >= 0:
                self.draw_piece_cell(x, y, self.current.kind)

    def draw_ghost(self):
        if self.current is None:
            return
        ghost_y = self.current.y
        while self.valid(self.current, y=ghost_y + 1):
            ghost_y += 1
        for x, y in self.current.cells(y=ghost_y):
            if y >= 0:
                self.draw_piece_cell(x, y, self.current.kind, ghost=True)

    def draw_hyena_animation(self):
        if not self.hyena_animation:
            return
        self.draw_piece_cell(
            self.hyena_animation["col"],
            self.hyena_animation["row"],
            HYENA_KIND,
        )

    def draw_piece_cell(self, grid_x, grid_y, kind, ghost=False, offset_x=0, offset_y=0, scale=1):
        color = ALL_COLORS[kind]
        if kind in DOG_KINDS:
            self.draw_dog_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        elif kind in SKULL_KINDS:
            self.draw_skull_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        elif kind == HYENA_KIND:
            self.draw_hyena_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        else:
            self.draw_cat_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)

    def draw_cat_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        x = offset_x + grid_x * CELL * scale
        y = offset_y + grid_y * CELL * scale
        size = CELL * scale
        pad = 3 * scale
        ear = 8 * scale
        outline = "#566070" if ghost else "#10131a"
        fill = "" if ghost else color
        width = 2 if not ghost else 1

        points_left = [x + pad + 3 * scale, y + pad + ear, x + pad + 8 * scale, y + pad, x + pad + 13 * scale, y + pad + ear]
        points_right = [x + size - pad - 13 * scale, y + pad + ear, x + size - pad - 8 * scale, y + pad, x + size - pad - 3 * scale, y + pad + ear]
        self.canvas.create_polygon(points_left, fill=fill, outline=outline, width=width)
        self.canvas.create_polygon(points_right, fill=fill, outline=outline, width=width)

        self.canvas.create_oval(
            x + pad,
            y + pad + 4 * scale,
            x + size - pad,
            y + size - pad,
            fill=fill,
            outline=outline,
            width=width,
        )

        if ghost:
            return

        eye_y = y + 15 * scale
        self.canvas.create_oval(x + 10 * scale, eye_y, x + 13 * scale, eye_y + 4 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 18 * scale, eye_y, x + 21 * scale, eye_y + 4 * scale, fill="#171b24", outline="")
        self.canvas.create_polygon(
            x + 15 * scale,
            y + 20 * scale,
            x + 18 * scale,
            y + 20 * scale,
            x + 16.5 * scale,
            y + 22.5 * scale,
            fill="#ff6f91",
            outline="",
        )
        self.canvas.create_line(x + 16.5 * scale, y + 22 * scale, x + 16.5 * scale, y + 24 * scale, fill="#171b24")
        self.canvas.create_line(x + 8 * scale, y + 21 * scale, x + 3 * scale, y + 19 * scale, fill="#171b24")
        self.canvas.create_line(x + 8 * scale, y + 24 * scale, x + 3 * scale, y + 25 * scale, fill="#171b24")
        self.canvas.create_line(x + 25 * scale, y + 21 * scale, x + 30 * scale, y + 19 * scale, fill="#171b24")
        self.canvas.create_line(x + 25 * scale, y + 24 * scale, x + 30 * scale, y + 25 * scale, fill="#171b24")

    def draw_dog_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        x = offset_x + grid_x * CELL * scale
        y = offset_y + grid_y * CELL * scale
        size = CELL * scale
        pad = 3 * scale
        outline = "#566070" if ghost else "#10131a"
        fill = "" if ghost else color
        width = 2 if not ghost else 1

        self.canvas.create_oval(
            x + pad,
            y + pad + 5 * scale,
            x + size - pad,
            y + size - pad,
            fill=fill,
            outline=outline,
            width=width,
        )
        self.canvas.create_oval(
            x + pad - 3 * scale,
            y + 8 * scale,
            x + 9 * scale,
            y + 22 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )
        self.canvas.create_oval(
            x + size - 9 * scale,
            y + 8 * scale,
            x + size - pad + 3 * scale,
            y + 22 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )

        if ghost:
            return

        eye_y = y + 15 * scale
        self.canvas.create_oval(x + 10 * scale, eye_y, x + 13 * scale, eye_y + 4 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 18 * scale, eye_y, x + 21 * scale, eye_y + 4 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 12 * scale, y + 20 * scale, x + 21 * scale, y + 27 * scale, fill="#f6dfc6", outline="#10131a", width=1)
        self.canvas.create_oval(x + 15 * scale, y + 20 * scale, x + 18 * scale, y + 23 * scale, fill="#171b24", outline="")
        self.canvas.create_arc(x + 13 * scale, y + 21 * scale, x + 17 * scale, y + 27 * scale, start=200, extent=115, style=tk.ARC, outline="#171b24")
        self.canvas.create_arc(x + 16 * scale, y + 21 * scale, x + 20 * scale, y + 27 * scale, start=225, extent=115, style=tk.ARC, outline="#171b24")

    def draw_skull_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        x = offset_x + grid_x * CELL * scale
        y = offset_y + grid_y * CELL * scale
        size = CELL * scale
        pad = 3 * scale
        outline = "#566070" if ghost else "#10131a"
        fill = "" if ghost else color
        width = 2 if not ghost else 1

        self.canvas.create_oval(
            x + pad,
            y + pad,
            x + size - pad,
            y + size - 7 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )
        self.canvas.create_rectangle(
            x + 9 * scale,
            y + 18 * scale,
            x + 24 * scale,
            y + 29 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )

        if ghost:
            return

        self.canvas.create_oval(x + 9 * scale, y + 11 * scale, x + 14 * scale, y + 17 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 19 * scale, y + 11 * scale, x + 24 * scale, y + 17 * scale, fill="#171b24", outline="")
        self.canvas.create_polygon(
            x + 16.5 * scale,
            y + 17 * scale,
            x + 14 * scale,
            y + 22 * scale,
            x + 19 * scale,
            y + 22 * scale,
            fill="#171b24",
            outline="",
        )
        for tooth_x in (11, 15, 19, 23):
            self.canvas.create_line(
                x + tooth_x * scale,
                y + 23 * scale,
                x + tooth_x * scale,
                y + 29 * scale,
                fill="#10131a",
            )
        self.canvas.create_line(x + 10 * scale, y + 23 * scale, x + 24 * scale, y + 23 * scale, fill="#10131a")

    def draw_hyena_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        x = offset_x + grid_x * CELL * scale
        y = offset_y + grid_y * CELL * scale
        size = CELL * scale
        pad = 3 * scale
        outline = "#566070" if ghost else "#10131a"
        fill = "" if ghost else color
        width = 2 if not ghost else 1

        self.canvas.create_polygon(
            x + 5 * scale,
            y + 12 * scale,
            x + 2 * scale,
            y + 3 * scale,
            x + 12 * scale,
            y + 8 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )
        self.canvas.create_polygon(
            x + size - 5 * scale,
            y + 12 * scale,
            x + size - 2 * scale,
            y + 3 * scale,
            x + size - 12 * scale,
            y + 8 * scale,
            fill=fill,
            outline=outline,
            width=width,
        )
        self.canvas.create_oval(
            x + pad,
            y + pad + 6 * scale,
            x + size - pad,
            y + size - pad,
            fill=fill,
            outline=outline,
            width=width,
        )

        if ghost:
            return

        self.canvas.create_polygon(
            x + 11 * scale,
            y + 20 * scale,
            x + 22 * scale,
            y + 20 * scale,
            x + 19 * scale,
            y + 27 * scale,
            x + 14 * scale,
            y + 27 * scale,
            fill="#f1d6a8",
            outline="#10131a",
            width=1,
        )
        self.canvas.create_oval(x + 9 * scale, y + 15 * scale, x + 12 * scale, y + 18 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 21 * scale, y + 15 * scale, x + 24 * scale, y + 18 * scale, fill="#171b24", outline="")
        self.canvas.create_oval(x + 15 * scale, y + 21 * scale, x + 18 * scale, y + 24 * scale, fill="#171b24", outline="")
        self.canvas.create_line(x + 11 * scale, y + 10 * scale, x + 14 * scale, y + 13 * scale, fill="#3b2f25", width=2)
        self.canvas.create_line(x + 19 * scale, y + 11 * scale, x + 22 * scale, y + 9 * scale, fill="#3b2f25", width=2)
        self.canvas.create_line(x + 6 * scale, y + 23 * scale, x + 2 * scale, y + 24 * scale, fill="#171b24")
        self.canvas.create_line(x + 27 * scale, y + 23 * scale, x + 31 * scale, y + 24 * scale, fill="#171b24")

    def draw_sidebar(self):
        x0 = BOARD_W
        self.canvas.create_rectangle(x0, 0, WINDOW_W, WINDOW_H, fill="#151820", outline="")
        self.canvas.create_text(x0 + 28, 35, text="Tetricat", anchor="w", fill="#f6f7fb", font=("Segoe UI", 22, "bold"))
        self.canvas.create_text(x0 + 28, 62, text=self.mode_title, anchor="w", fill="#aeb7c8", font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(x0 + 28, 80, text=f"Score\n{self.score}", anchor="nw", fill="#f6f7fb", font=("Segoe UI", 13, "bold"))
        self.canvas.create_text(x0 + 28, 145, text=f"Lignes\n{self.lines}", anchor="nw", fill="#f6f7fb", font=("Segoe UI", 13, "bold"))
        self.canvas.create_text(x0 + 28, 210, text=f"Niveau\n{self.level}", anchor="nw", fill="#f6f7fb", font=("Segoe UI", 13, "bold"))
        if self.hyena_notice:
            self.canvas.create_text(x0 + 28, 262, text=self.hyena_notice, anchor="nw", fill="#ffd166", font=("Segoe UI", 9, "bold"), width=130)
        self.canvas.create_text(x0 + 28, 285, text="Prochain", anchor="w", fill="#aeb7c8", font=("Segoe UI", 12, "bold"))

        preview_x = x0 + 34
        preview_y = 310
        preview_scale = 0.72
        for cx, cy in ALL_SHAPES[self.next_piece.kind][0]:
            self.draw_piece_cell(cx, cy, self.next_piece.kind, offset_x=preview_x, offset_y=preview_y, scale=preview_scale)

        music_label = "M musique off"
        if self.music.enabled and self.music.backend == "midi":
            music_label = "M musique midi"
        elif self.music.enabled and self.music.backend == "synth":
            music_label = "M musique douce"
        elif self.music.enabled and self.music.backend == "beep":
            music_label = "M musique simple"
        controls = ["<- -> bouger", "^ tourner", "v accelerer", "Espace poser", "P pause", music_label, "R reset", "Esc menu"]
        for index, line in enumerate(controls):
            self.canvas.create_text(
                x0 + 28,
                450 + index * 24,
                text=line,
                anchor="nw",
                fill="#aeb7c8",
                font=("Segoe UI", 11),
            )

    def draw_title_screen(self):
        self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill="#151820", outline="")
        self.canvas.create_rectangle(28, 28, WINDOW_W - 28, WINDOW_H - 28, fill="#1e2330", outline="#2b3140", width=2)
        self.canvas.create_text(WINDOW_W / 2, 92, text="Tetricat", fill="#f6f7fb", font=("Segoe UI", 42, "bold"))
        self.canvas.create_text(
            WINDOW_W / 2,
            140,
            text="Des chats, des chiens, des tetes de mort, et parfois une hyene.",
            fill="#aeb7c8",
            font=("Segoe UI", 13),
        )

        for x, kind in enumerate(["I", "O", "T"]):
            self.draw_piece_cell(x, 0, kind, offset_x=120, offset_y=178, scale=0.78)
        for x, kind in enumerate(["P", "U", "SK_PLUS", "SK_X"]):
            self.draw_piece_cell(x, 0, kind, offset_x=250, offset_y=178, scale=0.78)

        self.draw_menu_button(90, 275, "1  Mode classique", "Pieces standard en chats")
        self.draw_menu_button(90, 340, "2  Mode chaos", "Pieces standard + formes chiens")
        self.draw_menu_button(90, 405, "3  Mode crane", "Etoiles et carre creux en tetes de mort")
        self.draw_menu_button(90, 470, "4  Mode hyene", "Mode crane + surprises entre pieces")
        music_hint = "M pour couper/remettre la musique"
        if self.music.backend == "synth":
            music_hint = "MIDI indisponible: boucle douce active"
        elif self.music.backend == "beep":
            music_hint = "MIDI indisponible: mini synthese active"
        elif self.music.backend == "off":
            music_hint = "Musique indisponible ici"
        self.canvas.create_text(WINDOW_W / 2, 552, text="Clique un mode ou appuie sur 1 / 2 / 3 / 4", fill="#aeb7c8", font=("Segoe UI", 11))
        self.canvas.create_text(WINDOW_W / 2, 578, text=music_hint, fill="#aeb7c8", font=("Segoe UI", 10))

    def draw_menu_button(self, x, y, title, subtitle):
        self.canvas.create_rectangle(x, y, x + 300, y + 60, fill="#f6f7fb", outline="#10131a", width=2)
        self.canvas.create_text(x + 20, y + 18, text=title, anchor="w", fill="#10131a", font=("Segoe UI", 14, "bold"))
        self.canvas.create_text(x + 20, y + 42, text=subtitle, anchor="w", fill="#3c4658", font=("Segoe UI", 10))

    def draw_banner(self, title, subtitle):
        self.canvas.create_rectangle(24, 210, BOARD_W - 24, 330, fill="#10131a", outline="#f6f7fb", width=2)
        self.canvas.create_text(BOARD_W / 2, 250, text=title, fill="#f6f7fb", font=("Segoe UI", 24, "bold"))
        self.canvas.create_text(BOARD_W / 2, 292, text=subtitle, fill="#aeb7c8", font=("Segoe UI", 13))
