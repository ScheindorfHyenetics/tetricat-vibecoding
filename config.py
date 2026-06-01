# Dimensions logiques du plateau. Les pieces et collisions travaillent en cases,
# pas en pixels; CELL sert seulement a convertir la grille pour le rendu.
COLS = 10
ROWS = 20
CELL = 30
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDE_W = 180
WINDOW_W = BOARD_W + SIDE_W
WINDOW_H = BOARD_H

# Valeur sentinelle pour une case vide du plateau. On utilise `is EMPTY` dans le
# code pour distinguer clairement une case vide d'un type de piece.
EMPTY = None

# Delais de chute en millisecondes. FALL_MS est la gravite de depart, tandis que
# FAST_FALL_MS est utilise quand le joueur maintient la fleche bas.
FALL_MS = 520
FAST_FALL_MS = 45

# Barème Tetris classique pour 1 a 4 lignes; au-dela, game.py extrapole.
SCORE_BY_LINES = {1: 100, 2: 300, 3: 500, 4: 800}

# Probabilites des evenements apres le verrouillage d'une piece. En mode ghost,
# une hyene peut tomber avant une apparition de fantomes.
HYENA_CHANCE = 0.35
GHOST_CHANCE = 0.28

# Les fantomes evitent les toutes premieres lignes et explosent apres ce nombre
# de pieces verrouillees.
GHOST_SAFE_TOP_ROWS = 3
GHOST_LIFETIME_PIECES = 3

# Force la voie audio la plus fiable sur Windows quand le MIDI natif reste muet.
USE_RELIABLE_BEEP_PLAYBACK = True
