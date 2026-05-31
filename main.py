import base64
import ctypes
import math
import os
import random
import struct
import tempfile
import threading
import time
import tkinter as tk
import wave
from dataclasses import dataclass

try:
    import winsound
except ImportError:
    winsound = None


COLS = 10
ROWS = 20
CELL = 30
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDE_W = 180
WINDOW_W = BOARD_W + SIDE_W
WINDOW_H = BOARD_H

EMPTY = None
FALL_MS = 520
FAST_FALL_MS = 45

CAT_COLORS = {
    "I": "#71d6ff",
    "O": "#ffd166",
    "T": "#c084fc",
    "S": "#7bd88f",
    "Z": "#ff7b7b",
    "J": "#82aaff",
    "L": "#ffb86c",
}

DOG_COLORS = {
    "P": "#d7a86e",
    "U": "#f28f3b",
    "B": "#b08968",
    "Y": "#e76f51",
    "N": "#a3cef1",
}

SKULL_COLORS = {
    "SK_PLUS": "#e8e1d4",
    "SK_X": "#d8d2c8",
    "SK_RING": "#f0eadf",
}

HYENA_KIND = "H"
HYENA_COLOR = "#c7b07a"

STANDARD_SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

DOG_SHAPES = {
    "P": [
        [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)],
        [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (0, 1), (1, 1), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 0)],
    ],
    "U": [
        [(0, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 0), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "B": [
        [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1)],
        [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3)],
        [(2, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (0, 3)],
    ],
    "Y": [
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (0, 1), (1, 1), (2, 1), (0, 2)],
    ],
    "N": [
        [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (1, 1), (2, 1), (0, 2), (1, 2)],
    ],
}

SKULL_SHAPES = {
    "SK_PLUS": [
        [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
    ],
    "SK_X": [
        [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    ],
    "SK_RING": [
        [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)],
    ],
}

ALL_SHAPES = {**STANDARD_SHAPES, **DOG_SHAPES, **SKULL_SHAPES}
ALL_COLORS = {**CAT_COLORS, **DOG_COLORS, **SKULL_COLORS, HYENA_KIND: HYENA_COLOR}
DOG_KINDS = set(DOG_SHAPES)
SKULL_KINDS = set(SKULL_SHAPES)
SCORE_BY_LINES = {1: 100, 2: 300, 3: 500, 4: 800}
HYENA_CHANCE = 0.35
USE_RELIABLE_BEEP_PLAYBACK = True

MUSIC_MIDI_BASE64 = (
    "TVRoZAAAAAYAAQADAeBNVHJrAAAAEwD/UQMHoSAA/1gEBAIYCAD/LwBNVHJrAAABWADACgCwB14AkExegXCATAAAkE9egXCATwAA"
    "kFFegXCAUQAAkFNegXCAUwAAkFReg2CAVAAAkFNegXCAUwAAkFFegXCAUQAAkE9eg2CATwAAkExegXCATAAAkE9egXCATwAAkFFe"
    "g2CAUQAAkE9egXCATwAAkExegXCATAAAkEpegXCASgAAkExegXCATAAAkE9egXCATwAAkFFegXCAUQAAkFNeg2CAUwAAkFFegXCA"
    "UQAAkE9egXCATwAAkExeg2CATAAAkEhegXCASAAAkEpegXCASgAAkExeh0CATAAAkFFegXCAUQAAkFNegXCAUwAAkFZeg2CAVgAA"
    "kFRegXCAVAAAkFNegXCAUwAAkFFeg2CAUQAAkE9eg2CATwAAkExegXCATAAAkE9egXCATwAAkFNeg2CAUwAAkFFegXCAUQAAkE9e"
    "gXCATwAAkExeh0CATAAA/y8ATVRyawAAAZsAwQwAsQc6AJE8KgCRQCoAkUMqh0CBPAAAgUAAAIFDAACRPCoAkUEqAJFFKodAgTwAA"
    "IFBAACBRQAAkTkqAJE8KgCRQCqHQIE5AACBPAAAgUAAAJE5KgCRPioAkUIqh0CBOQAAgT4AAIFCAACRNSoAkTkqAJE8KodAgTUAA"
    "IE5AACBPAAAkTUqAJE7KgCRPiqHQIE1AACBOwAAgT4AAJE3KgCROyoAkT4qh0CBNwAAgTsAAIE+AACRNyoAkTwqAJFAKodAgTcAA"
    "IE8AACBQAAAkTwqAJFAKgCRQyqHQIE8AACBQAAAgUMAAJE8KgCRQSoAkUUqh0CBPAAAgUEAAIFFAACROSoAkTwqAJFAKodAgTkAA"
    "IE8AACBQAAAkTkqAJE+KgCRQiqHQIE5AACBPgAAgUIAAJE1KgCROSoAkTwqh0CBNQAAgTkAAIE8AACRNSoAkTsqAJE+KodAgTUAA"
    "IE7AACBPgAAkTcqAJE7KgCRPiqHQIE3AACBOwAAgT4AAJE3KgCRPCoAkUAqh0CBNwAAgTwAAIFAAAD/LwA="
)


class MidiMusic:
    def __init__(self):
        self.alias = "tetricat_music"
        self.path = None
        self.wav_path = None
        self.enabled = True
        self.available = hasattr(ctypes, "windll")
        self.backend = "midi" if self.available else "off"
        self.stop_beeps = threading.Event()
        self.beep_thread = None

    def play(self):
        if not self.enabled:
            return
        if USE_RELIABLE_BEEP_PLAYBACK and winsound is not None:
            self.start_beep_fallback()
            return
        if self.available:
            self.ensure_file()
            if self.path is not None:
                self.command(f'close {self.alias}')
                if self.command(f'open "{self.path}" type sequencer alias {self.alias}') == 0:
                    if self.command(f'play {self.alias} repeat') == 0:
                        self.backend = "midi"
                        return
        self.start_beep_fallback()

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.play()
        else:
            self.stop()

    def stop(self):
        self.stop_beeps.set()
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        if self.available:
            self.command(f'stop {self.alias}')
            self.command(f'close {self.alias}')
        self.backend = "off"

    def close(self):
        self.stop()
        if self.path and os.path.exists(self.path):
            try:
                os.remove(self.path)
            except OSError:
                pass
        if self.wav_path and os.path.exists(self.wav_path):
            try:
                os.remove(self.wav_path)
            except OSError:
                pass

    def ensure_file(self):
        if self.path and os.path.exists(self.path):
            return
        try:
            fd, path = tempfile.mkstemp(prefix="tetricat_", suffix=".mid")
            with os.fdopen(fd, "wb") as midi_file:
                midi_file.write(base64.b64decode(MUSIC_MIDI_BASE64))
            self.path = path
        except OSError:
            self.path = None
            self.available = False

    def command(self, text):
        try:
            return ctypes.windll.winmm.mciSendStringW(text, None, 0, None)
        except Exception:
            self.available = False
            return 1

    def start_beep_fallback(self):
        if winsound is None:
            self.backend = "off"
            return
        if self.start_soft_wav_loop():
            return
        if self.beep_thread and self.beep_thread.is_alive() and not self.stop_beeps.is_set():
            return
        self.stop_beeps.clear()
        self.backend = "beep"
        self.beep_thread = threading.Thread(target=self.beep_loop, daemon=True)
        self.beep_thread.start()

    def start_soft_wav_loop(self):
        try:
            self.ensure_wav_file()
            if self.wav_path is None:
                return False
            winsound.PlaySound(
                self.wav_path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
            )
            self.backend = "synth"
            return True
        except Exception:
            return False

    def ensure_wav_file(self):
        if self.wav_path and os.path.exists(self.wav_path):
            return
        try:
            fd, path = tempfile.mkstemp(prefix="tetricat_soft_", suffix=".wav")
            os.close(fd)
            self.write_soft_wav(path)
            self.wav_path = path
        except OSError:
            self.wav_path = None

    def write_soft_wav(self, path):
        sample_rate = 22050
        bpm = 86
        beat = 60.0 / bpm
        notes = {
            "REST": 0,
            "C3": 130.81,
            "D3": 146.83,
            "E3": 164.81,
            "F3": 174.61,
            "G3": 196.00,
            "A3": 220.00,
            "B3": 246.94,
            "C4": 261.63,
            "D4": 293.66,
            "E4": 329.63,
            "F4": 349.23,
            "G4": 392.00,
            "A4": 440.00,
        }
        progression = [
            ("C3", "G3", "C4"),
            ("A3", "E3", "C4"),
            ("F3", "C4", "A3"),
            ("G3", "D4", "B3"),
            ("E3", "B3", "G3"),
            ("F3", "C4", "A3"),
            ("D3", "A3", "F3"),
            ("G3", "D4", "B3"),
        ]
        melody = [
            "E4", "REST", "G4", "REST", "A4", "G4", "E4", "REST",
            "D4", "REST", "E4", "G4", "C4", "REST", "REST", "REST",
            "A3", "C4", "E4", "REST", "G4", "E4", "D4", "REST",
            "C4", "REST", "D4", "E4", "G3", "REST", "REST", "REST",
            "E4", "D4", "C4", "REST", "A3", "C4", "D4", "REST",
            "E4", "REST", "G4", "A4", "G4", "REST", "REST", "REST",
            "C4", "REST", "D4", "E4", "F4", "E4", "C4", "REST",
            "B3", "REST", "D4", "G4", "C4", "REST", "REST", "REST",
        ]
        frames = []
        step_seconds = beat * 0.5
        total_steps = len(melody)
        samples_per_step = int(sample_rate * step_seconds)

        def envelope(pos, length):
            attack = max(1, int(length * 0.08))
            release = max(1, int(length * 0.22))
            if pos < attack:
                return pos / attack
            if pos > length - release:
                return max(0.0, (length - pos) / release)
            return 1.0

        for step, note_name in enumerate(melody):
            chord = progression[(step // 8) % len(progression)]
            melody_freq = notes[note_name]
            chord_freqs = [notes[name] for name in chord]
            for i in range(samples_per_step):
                t = i / sample_rate
                env = envelope(i, samples_per_step)
                bass = math.sin(2 * math.pi * chord_freqs[0] * 0.5 * t) * 0.13
                pad = sum(math.sin(2 * math.pi * freq * t) for freq in chord_freqs) * 0.035
                lead = 0.0
                if melody_freq:
                    lead = math.sin(2 * math.pi * melody_freq * t) * 0.09
                    lead += math.sin(2 * math.pi * melody_freq * 2 * t) * 0.015
                value = (bass + pad + lead) * env
                frames.append(struct.pack("<h", int(max(-0.8, min(0.8, value)) * 32767)))

        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"".join(frames))

    def beep_loop(self):
        tune = [
            (330, 360), (392, 360), (440, 540), (392, 360),
            (330, 540), (294, 360), (330, 720), (262, 720),
            (220, 360), (262, 360), (330, 540), (392, 360),
            (349, 540), (330, 360), (294, 720), (262, 720),
            (330, 360), (294, 360), (262, 540), (220, 360),
            (262, 540), (294, 360), (330, 720), (392, 720),
            (262, 360), (294, 360), (330, 540), (349, 360),
            (330, 540), (262, 360), (247, 720), (262, 960),
        ]
        while not self.stop_beeps.is_set() and self.enabled:
            for freq, duration in tune:
                if self.stop_beeps.is_set() or not self.enabled:
                    break
                winsound.Beep(freq, duration)
                time.sleep(0.08)
            time.sleep(0.65)


@dataclass
class Piece:
    kind: str
    x: int = 3
    y: int = 0
    rotation: int = 0

    @property
    def color(self):
        return ALL_COLORS[self.kind]

    def cells(self, rotation=None, x=None, y=None):
        rotation = self.rotation if rotation is None else rotation
        x = self.x if x is None else x
        y = self.y if y is None else y
        shape = ALL_SHAPES[self.kind][rotation % len(ALL_SHAPES[self.kind])]
        return [(x + cx, y + cy) for cx, cy in shape]


class Tetricat:
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

        self.root.bind("<Left>", lambda _: self.move(-1, 0))
        self.root.bind("<Right>", lambda _: self.move(1, 0))
        self.root.bind("<Down>", self.start_soft_drop)
        self.root.bind("<KeyRelease-Down>", self.stop_soft_drop)
        self.root.bind("<Up>", lambda _: self.rotate())
        self.root.bind("<space>", lambda _: self.hard_drop())
        self.root.bind("p", lambda _: self.toggle_pause())
        self.root.bind("m", lambda _: self.toggle_music())
        self.root.bind("r", lambda _: self.restart())
        self.root.bind("1", lambda _: self.start_game("classic"))
        self.root.bind("2", lambda _: self.start_game("chaos"))
        self.root.bind("3", lambda _: self.start_game("skull"))
        self.root.bind("4", lambda _: self.start_game("hyena"))
        self.root.bind("<Escape>", lambda _: self.show_menu())
        self.canvas.bind("<Button-1>", self.handle_click)

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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Tetricat().run()
