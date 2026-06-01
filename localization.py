import json
from pathlib import Path


# Les fichiers de traduction vivent a cote du code pour que le jeu reste
# portable: copier le dossier suffit, sans installation de package externe.
LOCALES_DIR = Path(__file__).with_name("locales")

# Ordre d'affichage de l'ecran de langue. Le code court sert au nom du fichier
# JSON, le libelle lisible sert aux menus et aux controles clavier.
LANGUAGES = [
    ("en", "English"),
    ("fr", "Francais"),
    ("es", "Espanol"),
    ("de", "Deutsch"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
]


class Localizer:
    """Charge une langue et fournit les textes traduits au reste du jeu."""

    def __init__(self, language="en"):
        self.language = language
        self.translations = {}
        self.set_language(language)

    def set_language(self, language):
        # Chaque changement remplace tout le dictionnaire courant. C'est simple
        # et suffisant ici, car les fichiers sont petits et charges une seule fois
        # au lancement ou quand le joueur choisit une langue.
        self.language = language
        with (LOCALES_DIR / f"{language}.json").open(encoding="utf-8") as locale_file:
            self.translations = json.load(locale_file)

    def text(self, key, **values):
        # En cas de cle manquante, on affiche la cle elle-meme: cela rend les
        # oublis visibles a l'ecran sans faire planter la partie.
        value = self.translations.get(key, key)
        if values:
            # Les valeurs nommees servent pour les messages dynamiques, par
            # exemple le numero de colonne ou le compte a rebours des fantomes.
            return value.format(**values)
        return value
