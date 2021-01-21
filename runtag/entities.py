from .equipments import Compass, Radio, Telescope
from .station import Message, Station
from .types import Entity


class Person(Entity):
    def move(self, direction):
        if direction is None:
            return # no-op

        self.grid.move(self, direction)


class Soldier(Person):
    rank = None

    def __init__(self, grid, squad=None):
        super().__init__(grid)
        self.squad = squad
        self.radio = Radio(grid, self)

    def is_friendly(self, soldier):
        return self.squad is soldier.squad

    def is_enemy(self, soldier):
        return self.squad is not soldier.squad

    @property
    def alongside(self):
        entities = self.grid.entities_with(self)
        entities.remove(self)
        return entities


class Commander(Soldier):
    rank = 'commander'

    def __init__(self, grid, squad=None):
        super().__init__(grid, squad)
        self.position = None
        self.observation = None

        self.compass = Compass(grid, self)
        self.telescope = Telescope(grid, self)

    def observe(self):
        self.position = self.compass.operate()
        self.observation = self.telescope.operate()
        return self.observation

    def move(self, direction):
        super().move(direction)
        self.position = self.compass.operate()
        return self.position

    def command(self, target, direction):
        self.radio.operate(receiver=target, payload=direction)

    @property
    def tagged(self):
        for soldier in self.alongside:
            if self.is_enemy(soldier) and (soldier.rank == 'subordinate'):
                return True
        return False

class Subordinate(Soldier):
    rank = 'subordinate'

    def __init__(self, grid, squad=None, identifier=0):
        super().__init__(grid, squad)
        self.identifier = identifier
        self.direction = None

    def listen(self):
        payloads = self.radio.operate()
        self.direction = payloads[0] if payloads else None
        return self.direction

    def move(self, direction):
        super().move(direction)
        self.direction = None

    @property
    def taggable(self):
        for soldier in self.alongside:
            if self.is_enemy(soldier) and (soldier.rank == 'commander'):
                return True
        return False


class Squad(Entity):
    def __init__(self, grid, name):
        super().__init__(grid)
        self.name = name
        self.commander = None
        self.subordinates = []

    def assign(self, soldier):
        soldier.squad = self

        if soldier.rank == 'commander':
            self.commander = soldier
        elif soldier.rank == 'subordinate':
            self.subordinates.append(soldier)
        else:
            raise ValueError('soldier should be either Commander or Subordinate')

    @property
    def soldiers(self):
        return [self.commander] + self.subordinates