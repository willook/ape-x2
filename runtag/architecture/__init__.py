class BaseRunTag:
    def __init__(self, game, on_tick=None):
        self.game = game
        self.on_tick = on_tick

    def run(self):
        raise NotImplementedError()

    def tick(self):
        raise NotImplementedError()