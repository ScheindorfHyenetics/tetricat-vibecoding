import base64
import ctypes
import math
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import wave

from config import USE_RELIABLE_BEEP_PLAYBACK

try:
    import winsound
except ImportError:
    winsound = None

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
        self.external_process = None
        self.external_player = self.find_external_player()

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

    def play_explosion(self):
        if winsound is None and self.external_player is None:
            return
        threading.Thread(target=self.play_explosion_sound, daemon=True).start()

    def stop(self):
        self.stop_beeps.set()
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        self.stop_external_player()
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
        if self.start_soft_wav_loop():
            return
        if winsound is None:
            self.backend = "off"
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
            if winsound is not None:
                winsound.PlaySound(
                    self.wav_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
                )
                self.backend = "synth"
                return True
            return self.start_external_wav_loop()
        except Exception:
            return False

    def find_external_player(self):
        candidates = (
            ("paplay", ["paplay"]),
            ("pw-play", ["pw-play"]),
            ("aplay", ["aplay", "-q"]),
            ("afplay", ["afplay"]),
            ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
        )
        for executable, command in candidates:
            if shutil.which(executable):
                return command
        return None

    def start_external_wav_loop(self):
        if self.external_player is None:
            return False
        if self.beep_thread and self.beep_thread.is_alive() and not self.stop_beeps.is_set():
            return True
        self.stop_beeps.clear()
        self.backend = "synth"
        self.beep_thread = threading.Thread(target=self.external_wav_loop, daemon=True)
        self.beep_thread.start()
        return True

    def external_wav_loop(self):
        while not self.stop_beeps.is_set() and self.enabled and self.wav_path:
            command = [*self.external_player, self.wav_path]
            try:
                self.external_process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                while self.external_process.poll() is None:
                    if self.stop_beeps.wait(0.1) or not self.enabled:
                        self.stop_external_player()
                        return
            except Exception:
                self.backend = "off"
                return
            finally:
                self.external_process = None

    def stop_external_player(self):
        process = self.external_process
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=0.8)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

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

    def explosion_beeps(self):
        for freq, duration in ((180, 55), (125, 70), (85, 120)):
            try:
                winsound.Beep(freq, duration)
            except Exception:
                return
            time.sleep(0.025)

    def play_explosion_sound(self):
        if winsound is not None:
            self.explosion_beeps()
            return
        if self.external_player is None:
            return
        fd, path = tempfile.mkstemp(prefix="tetricat_explosion_", suffix=".wav")
        os.close(fd)
        try:
            self.write_explosion_wav(path)
            subprocess.run(
                [*self.external_player, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
            )
        except Exception:
            pass
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def write_explosion_wav(self, path):
        sample_rate = 22050
        frames = []
        for freq, seconds in ((180, 0.055), (125, 0.07), (85, 0.12)):
            samples = int(sample_rate * seconds)
            for i in range(samples):
                t = i / sample_rate
                fade = max(0.0, 1.0 - (i / max(1, samples)))
                noise = math.sin(2 * math.pi * freq * t) * 0.45 * fade
                frames.append(struct.pack("<h", int(noise * 32767)))
            frames.extend(struct.pack("<h", 0) for _ in range(int(sample_rate * 0.025)))
        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"".join(frames))
