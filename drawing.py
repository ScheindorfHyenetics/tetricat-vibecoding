import tkinter as tk
import tkinter.font as tkfont

from config import BOARD_H, BOARD_W, CELL, COLS, EMPTY, ROWS, WINDOW_H, WINDOW_W
from localization import LANGUAGES
from pieces import ALL_COLORS, ALL_SHAPES, DOG_KINDS, GHOST_KIND, HYENA_KIND, SKULL_KINDS


FONT_CANDIDATES = ("Segoe UI", "Noto Sans", "DejaVu Sans", "Liberation Sans", "Arial")


class TetricatDrawing:
    def font(self, size, weight=None):
        if not hasattr(self, "_ui_font_family"):
            available = {name.lower(): name for name in tkfont.families(self.root)}
            self._ui_font_family = next(
                (available[name.lower()] for name in FONT_CANDIDATES if name.lower() in available),
                "TkDefaultFont",
            )
        if weight is None:
            return (self._ui_font_family, size)
        return (self._ui_font_family, size, weight)

    def draw(self):
        # Point d'entree unique du rendu. Chaque appel reconstruit toute l'image
        # du canvas; cela evite d'avoir a synchroniser des elements graphiques
        # persistants avec l'etat du jeu.
        self.canvas.delete("all")
        if not self.language_selected:
            self.draw_language_screen()
            return
        if self.mode is None:
            self.draw_title_screen()
            return
        self.draw_board_background()
        self.draw_landed_pieces()
        if self.current is not None:
            self.draw_ghost()
            self.draw_current_piece()
        self.draw_hyena_animation()
        self.draw_ghost_animation()
        self.draw_sidebar()

        # Les bannieres sont dessinees en dernier pour rester au-dessus du
        # plateau et de la sidebar.
        if self.paused:
            self.draw_banner(self.t("pause_title"), self.t("pause_subtitle"))
        elif self.game_over:
            self.draw_banner(self.t("game_over_title"), self.t("game_over_subtitle"))

    def draw_board_background(self):
        # Le plateau occupe la partie gauche de la fenetre. La grille est purement
        # visuelle: les collisions utilisent self.board dans game.py.
        self.canvas.create_rectangle(0, 0, BOARD_W, BOARD_H, fill="#1e2330", outline="")
        for x in range(COLS + 1):
            px = x * CELL
            self.canvas.create_line(px, 0, px, BOARD_H, fill="#2b3140")
        for y in range(ROWS + 1):
            py = y * CELL
            self.canvas.create_line(0, py, BOARD_W, py, fill="#2b3140")

    def draw_landed_pieces(self):
        # Parcourt le plateau logique et dessine uniquement les cases occupees.
        for y, row in enumerate(self.board):
            for x, kind in enumerate(row):
                if kind is not EMPTY:
                    self.draw_piece_cell(x, y, kind)

    def draw_current_piece(self):
        # La piece active n'est pas encore inscrite dans self.board, elle est donc
        # dessinee separement par-dessus les pieces deja posees.
        for x, y in self.current.cells():
            if y >= 0:
                self.draw_piece_cell(x, y, self.current.kind)

    def draw_ghost(self):
        # Ombre de chute: on simule la descente jusqu'a collision sans modifier
        # la piece active, puis on dessine cette position en contour.
        if self.current is None:
            return
        ghost_y = self.current.y
        while self.valid(self.current, y=ghost_y + 1):
            ghost_y += 1
        for x, y in self.current.cells(y=ghost_y):
            if y >= 0:
                self.draw_piece_cell(x, y, self.current.kind, ghost=True)

    def draw_hyena_animation(self):
        # Pendant l'animation, la hyene est stockee avec une ligne flottante. Les
        # fonctions de dessin acceptent ces coordonnees pour produire un mouvement
        # fluide entre deux cases.
        if not self.hyena_animation:
            return
        self.draw_piece_cell(
            self.hyena_animation["col"],
            self.hyena_animation["row"],
            HYENA_KIND,
        )

    def draw_ghost_animation(self):
        # Le bloc fantome apparait progressivement: `progress` de 0 a 1 decide le
        # nombre de cellules deja visibles dans le carre 2x2.
        if not self.ghost_animation:
            return
        col = self.ghost_animation["col"]
        row = self.ghost_animation["row"]
        visible_cells = max(1, int(self.ghost_animation["progress"] * 4 + 0.999))
        for index, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
            if index < visible_cells:
                self.draw_piece_cell(col + dx, row + dy, GHOST_KIND)

    def draw_piece_cell(self, grid_x, grid_y, kind, ghost=False, offset_x=0, offset_y=0, scale=1):
        # Dispatch visuel par famille de piece. La logique du jeu manipule des
        # codes ("I", "P", "SK_PLUS"...), et cette methode choisit le dessin
        # adapte sans que game.py connaisse les details graphiques.
        color = ALL_COLORS[kind]
        if kind in DOG_KINDS:
            self.draw_dog_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        elif kind in SKULL_KINDS:
            self.draw_skull_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        elif kind == HYENA_KIND:
            self.draw_hyena_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        elif kind == GHOST_KIND:
            self.draw_ghost_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)
        else:
            self.draw_cat_cell(grid_x, grid_y, color, ghost=ghost, offset_x=offset_x, offset_y=offset_y, scale=scale)

    def draw_cat_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        # Toutes les cellules utilisent le meme systeme de coordonnees:
        # grille -> pixels, avec un offset/scale pour les apercus de menu.
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
            # En mode ombre, seul le contour est dessine pour ne pas confondre
            # l'apercu avec une vraie piece posee.
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
        # Variante chien: meme boite de collision qu'une cellule normale, seul le
        # dessin interne change.
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
        # Variante crane pour les pieces speciales du mode skull et au-dela.
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
        # La hyene est dessinee comme une cellule speciale, ce qui permet de la
        # reutiliser a la fois pendant l'animation et une fois posee sur le board.
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

    def draw_ghost_cell(self, grid_x, grid_y, color, ghost=False, offset_x=0, offset_y=0, scale=1):
        # Les fantomes ont un contour clair pour rester lisibles meme quand ils
        # remplacent des pieces colorees.
        x = offset_x + grid_x * CELL * scale
        y = offset_y + grid_y * CELL * scale
        size = CELL * scale
        outline = "#d9fbff" if not ghost else "#566070"
        fill = "" if ghost else color
        width = 2 if not ghost else 1

        body = [
            x + 4 * scale,
            y + 13 * scale,
            x + 5 * scale,
            y + 8 * scale,
            x + 9 * scale,
            y + 4 * scale,
            x + size - 9 * scale,
            y + 4 * scale,
            x + size - 5 * scale,
            y + 8 * scale,
            x + size - 4 * scale,
            y + 13 * scale,
            x + size - 4 * scale,
            y + size - 5 * scale,
            x + 23 * scale,
            y + 25 * scale,
            x + 17 * scale,
            y + size - 4 * scale,
            x + 11 * scale,
            y + 25 * scale,
            x + 4 * scale,
            y + size - 5 * scale,
        ]
        self.canvas.create_polygon(body, fill=fill, outline=outline, width=width, smooth=True)

        if ghost:
            return

        self.canvas.create_oval(x + 10 * scale, y + 12 * scale, x + 14 * scale, y + 18 * scale, fill="#15202b", outline="")
        self.canvas.create_oval(x + 20 * scale, y + 12 * scale, x + 24 * scale, y + 18 * scale, fill="#15202b", outline="")
        self.canvas.create_oval(x + 14 * scale, y + 20 * scale, x + 20 * scale, y + 24 * scale, fill="#15202b", outline="")

    def draw_sidebar(self):
        # La sidebar affiche l'etat courant de la partie et les controles. Les
        # textes passent tous par self.t() pour suivre la langue choisie.
        x0 = BOARD_W
        self.canvas.create_rectangle(x0, 0, WINDOW_W, WINDOW_H, fill="#151820", outline="")
        self.canvas.create_text(x0 + 28, 35, text=self.t("title"), anchor="w", fill="#f6f7fb", font=self.font(22, "bold"))
        self.canvas.create_text(x0 + 28, 62, text=self.mode_title, anchor="w", fill="#aeb7c8", font=self.font(10, "bold"))
        self.canvas.create_text(x0 + 28, 80, text=f"{self.t('score')}\n{self.score}", anchor="nw", fill="#f6f7fb", font=self.font(13, "bold"))
        self.canvas.create_text(x0 + 28, 145, text=f"{self.t('lines')}\n{self.lines}", anchor="nw", fill="#f6f7fb", font=self.font(13, "bold"))
        self.canvas.create_text(x0 + 28, 210, text=f"{self.t('level')}\n{self.level}", anchor="nw", fill="#f6f7fb", font=self.font(13, "bold"))
        if self.event_notice:
            self.canvas.create_text(x0 + 28, 262, text=self.event_notice, anchor="nw", fill="#ffd166", font=self.font(9, "bold"), width=130)
        self.canvas.create_text(x0 + 28, 285, text=self.t("next"), anchor="w", fill="#aeb7c8", font=self.font(12, "bold"))

        preview_x = x0 + 34
        preview_y = 310
        preview_scale = 0.72
        # Apercu de la piece suivante: les coordonnees de forme sont reutilisees
        # avec un offset et un scale plus petit.
        for cx, cy in ALL_SHAPES[self.next_piece.kind][0]:
            self.draw_piece_cell(cx, cy, self.next_piece.kind, offset_x=preview_x, offset_y=preview_y, scale=preview_scale)

        music_label = self.t("music_off")
        if self.music.enabled and self.music.backend == "midi":
            music_label = self.t("music_midi")
        elif self.music.enabled and self.music.backend == "synth":
            music_label = self.t("music_synth")
        elif self.music.enabled and self.music.backend == "beep":
            music_label = self.t("music_beep")
        controls = [
            self.t("control_move"),
            self.t("control_rotate"),
            self.t("control_soft_drop"),
            self.t("control_hard_drop"),
            self.t("control_pause"),
            music_label,
            self.t("control_reset"),
            self.t("control_menu"),
        ]
        for index, line in enumerate(controls):
            self.canvas.create_text(
                x0 + 28,
                450 + index * 24,
                text=line,
                anchor="nw",
                fill="#aeb7c8",
                font=self.font(11),
            )

    def draw_language_screen(self):
        # Premier ecran affiche au lancement. Les boutons sont en grille 2x3; les
        # memes coordonnees sont reprises par game.handle_click().
        self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill="#151820", outline="")
        self.canvas.create_rectangle(28, 28, WINDOW_W - 28, WINDOW_H - 28, fill="#1e2330", outline="#2b3140", width=2)
        self.canvas.create_text(WINDOW_W / 2, 92, text=self.t("title"), fill="#f6f7fb", font=self.font(42, "bold"))
        self.canvas.create_text(WINDOW_W / 2, 150, text=self.t("language_title"), fill="#aeb7c8", font=self.font(18, "bold"))

        labels = {
            "en": "English",
            "fr": "Francais",
            "es": "Espanol",
            "de": "Deutsch",
            # Echappements Unicode pour eviter les problemes d'encodage dans les
            # consoles Windows tout en affichant les noms natifs dans Tkinter.
            "ja": "\u65e5\u672c\u8a9e",
            "zh": "\u4e2d\u6587",
        }
        for index, (code, _) in enumerate(LANGUAGES):
            row = index // 2
            col = index % 2
            x = 70 + col * 175
            y = 245 + row * 78
            self.draw_menu_button(x, y, f"{index + 1}  {labels[code]}", "")

        self.canvas.create_text(WINDOW_W / 2, 525, text=self.t("language_hint"), fill="#aeb7c8", font=self.font(11))

    def draw_title_screen(self):
        # Menu principal apres le choix de langue. Il n'affiche aucun etat de
        # partie: cliquer ou presser 1-5 appelle start_game().
        self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill="#151820", outline="")
        self.canvas.create_rectangle(28, 28, WINDOW_W - 28, WINDOW_H - 28, fill="#1e2330", outline="#2b3140", width=2)
        self.canvas.create_text(WINDOW_W / 2, 92, text=self.t("title"), fill="#f6f7fb", font=self.font(42, "bold"))
        self.canvas.create_text(
            WINDOW_W / 2,
            140,
            text=self.t("intro"),
            fill="#aeb7c8",
            font=self.font(13),
        )

        for x, kind in enumerate(["I", "O", "T"]):
            self.draw_piece_cell(x, 0, kind, offset_x=120, offset_y=178, scale=0.78)
        for x, kind in enumerate(["P", "U", "SK_PLUS", "SK_X"]):
            self.draw_piece_cell(x, 0, kind, offset_x=250, offset_y=178, scale=0.78)

        self.draw_menu_button(90, 250, self.t("menu_classic_title"), self.t("menu_classic_subtitle"))
        self.draw_menu_button(90, 305, self.t("menu_chaos_title"), self.t("menu_chaos_subtitle"))
        self.draw_menu_button(90, 360, self.t("menu_skull_title"), self.t("menu_skull_subtitle"))
        self.draw_menu_button(90, 415, self.t("menu_hyena_title"), self.t("menu_hyena_subtitle"))
        self.draw_menu_button(90, 470, self.t("menu_ghost_title"), self.t("menu_ghost_subtitle"))
        music_hint = self.t("music_toggle_hint")
        if self.music.backend == "synth":
            music_hint = self.t("music_synth_hint")
        elif self.music.backend == "beep":
            music_hint = self.t("music_beep_hint")
        elif self.music.backend == "off":
            music_hint = self.t("music_off_hint")
        self.canvas.create_text(WINDOW_W / 2, 552, text=self.t("menu_hint"), fill="#aeb7c8", font=self.font(11))
        self.canvas.create_text(WINDOW_W / 2, 578, text=music_hint, fill="#aeb7c8", font=self.font(10))

    def draw_menu_button(self, x, y, title, subtitle):
        # Bouton simple dessine dans le canvas. Tkinter Canvas ne fournit pas de
        # widgets boutons stylables ici, donc les zones cliquables sont gerees
        # manuellement dans game.handle_click().
        self.canvas.create_rectangle(x, y, x + 300, y + 60, fill="#f6f7fb", outline="#10131a", width=2)
        self.canvas.create_text(x + 20, y + 18, text=title, anchor="w", fill="#10131a", font=self.font(14, "bold"))
        self.canvas.create_text(x + 20, y + 42, text=subtitle, anchor="w", fill="#3c4658", font=self.font(10))

    def draw_banner(self, title, subtitle):
        # Overlay centre utilise pour pause et game over.
        self.canvas.create_rectangle(24, 210, BOARD_W - 24, 330, fill="#10131a", outline="#f6f7fb", width=2)
        self.canvas.create_text(BOARD_W / 2, 250, text=title, fill="#f6f7fb", font=self.font(24, "bold"))
        self.canvas.create_text(BOARD_W / 2, 292, text=subtitle, fill="#aeb7c8", font=self.font(13))
