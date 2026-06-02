def bind_user_inputs(game):
    # Toute l'entree clavier reste centralisee ici. Les fonctions appelees sont
    # responsables d'ignorer l'action si l'etat du jeu ne l'autorise pas
    # (pause, menu, animation speciale, fin de partie, etc.).
    game.root.bind("<Left>", lambda _: game.move(-1, 0))
    game.root.bind("<Right>", lambda _: game.move(1, 0))

    # La chute acceleree est maintenue tant que la touche bas reste enfoncee.
    game.root.bind("<Down>", game.start_soft_drop)
    game.root.bind("<KeyRelease-Down>", game.stop_soft_drop)

    game.root.bind("<Up>", lambda _: game.rotate())
    game.root.bind("<space>", lambda _: game.hard_drop())
    game.root.bind("p", lambda _: game.toggle_pause())
    game.root.bind("m", lambda _: game.toggle_music())
    game.root.bind("r", lambda _: game.restart())

    # Les chiffres ont deux roles: avant le choix de langue ils selectionnent
    # une localisation, puis ils lancent les modes de jeu.
    for number in range(1, 7):
        game.root.bind(str(number), lambda _, value=number: game.handle_number(value))
        game.root.bind(f"<KP_{number}>", lambda _, value=number: game.handle_number(value))

    # Escape ne change pas la langue: il ramene seulement au menu des modes.
    game.root.bind("<Escape>", lambda _: game.show_menu())
    game.canvas.bind("<Button-1>", game.handle_click)
