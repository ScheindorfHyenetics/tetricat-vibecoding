import json
from pathlib import Path


LOCALES_DIR = Path(__file__).with_name("locales")

LANGUAGES = [
    ("en", "English"),
    ("fr", "Francais"),
    ("es", "Espanol"),
    ("de", "Deutsch"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
]


class Localizer:
    def __init__(self, language="en"):
        self.language = language
        self.translations = {}
        self.set_language(language)

    def set_language(self, language):
        self.language = language
        with (LOCALES_DIR / f"{language}.json").open(encoding="utf-8") as locale_file:
            self.translations = json.load(locale_file)

    def text(self, key, **values):
        value = self.translations.get(key, key)
        if values:
            return value.format(**values)
        return value
