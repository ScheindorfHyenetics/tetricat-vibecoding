# Tetricat

Un petit clone de Tetris en Python ou les briques sont des chats, avec des modes bonus ou les pieces deviennent des chiens, des tetes de mort, puis des hyenes et des fantomes viennent semer le bazar.

## Lancer le jeu

```powershell
python main.py
```

## Controles

- 1: lancer le mode classique
- 2: lancer le mode chaos
- 3: lancer le mode crane
- 4: lancer le mode hyene
- 5: lancer le mode fantome
- Fleches gauche / droite: deplacer la piece
- Fleche haut: tourner
- Fleche bas: accelerer la chute
- Espace: poser la piece directement
- P: pause
- M: couper ou remettre la musique
- R: recommencer
- Esc: revenir au menu

## Musique

Le jeu contient une petite musique MIDI originale encodee directement dans le code. Comme le lecteur MIDI Windows peut rester muet selon la machine, le jeu utilise par defaut une boucle WAV generee au lancement: plus longue, plus douce, et moins repetitive qu'une simple suite de bips.

## Modes

- Mode classique: les 7 pieces standard de Tetris, dessinees en chats.
- Mode chaos: les pieces standard en chats, plus des pieces non standard dessinees en chiens.
- Mode crane: le mode chaos, plus des pieces speciales dessinees en tetes de mort: une croix, une etoile diagonale, et un carre 3x3 avec un trou au centre.
- Mode hyene: le mode crane, avec parfois une hyene entre deux pieces. On la voit tomber dans une colonne au hasard, puis elle peut ajouter une case ou detruire quelques cases autour de son impact.
- Mode fantome: le mode crane, avec parfois un bloc 2x2 de fantomes qui apparait progressivement hors des trois lignes du haut. Il peut remplacer des cases existantes, puis explose brutalement apres trois autres pieces tombees.
