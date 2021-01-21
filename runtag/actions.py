from .entities import Subordinate


class Action:
    def act(self, actor):
        raise NotImplementedError()

    def __repr__(self):
        properties = [f'{key}={repr(value)}' for key, value in vars(self).items()]
        return f'{type(self).__name__}({", ".join(properties)})'


class CommanderObserve(Action):
    def act(self, actor):
        return actor.observe()


class CommanderMove(Action):
    def __init__(self, direction):
        self.direction = direction

    def act(self, actor):
        return actor.move(self.direction)


class CommanderCommand(Action):
    def __init__(self, subordinate, direction):
        self.subordinate = subordinate
        self.direction = direction

    def act(self, actor):
        return actor.command(self.as_subordinate(actor.squad, self.subordinate),
                             self.direction)

    def as_subordinate(self, squad, subordinate):
        if isinstance(subordinate, Subordinate):
            return subordinate
        return squad.subordinates[subordinate]


class SubordinateListen(Action):
    def act(self, actor):
        return actor.listen()


class SubordinateMove(Action):
    def __init__(self, direction):
        self.direction = direction

    def act(self, actor):
        actor.move(self.direction)