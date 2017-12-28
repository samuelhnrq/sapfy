import jack

J_CLIENT = jack.Client('Sapfy')
MUSIC_L: jack.OwnPort = J_CLIENT.inports.register(
    'sapper-left', is_terminal=True)
MUSIC_R: jack.OwnPort = J_CLIENT.inports.register(
    'sapper-right', is_terminal=True)
