from collections import OrderedDict

from .bootcamp import Bootcamp
from .entities import Subordinate
from .formation import Formation
from .grid import Grid
from .station import Station
from .types import Position


class Game:
    def __init__(self, width, height):
        self.grid = Grid(width, height)
        self.camps = OrderedDict()

    @classmethod
    def make(cls, width, height, number_of_subordinates):
        while True:
            game = cls(width, height)

            camps = ['blue', 'red']
            bootcamp = Bootcamp(game.grid)
            formation = Formation(game.grid)

            positioner = formation.place(number_of_camps=len(camps),
                                        number_of_soldiers=1 + number_of_subordinates)
            for camp in camps:
                squad = bootcamp.recruit(name=camp, number_of_subordinates=number_of_subordinates)
                game.camps[squad.name] = squad

                commander_position, *subordinate_positions = next(positioner)
                game.spawn(squad, commander_position, subordinate_positions)

            if game.done:
                continue

            return game

    def spawn(self, squad, commander_position, subordinate_positions):
        self.grid.add(commander_position, squad.commander)

        for subordinate_position, subordinate in zip(subordinate_positions, squad.subordinates):
            self.grid.add(subordinate_position, subordinate)

    def entities(self, type=object):
        return [entity for entity in self.grid.entities.keys()
                       if isinstance(entity, type)]

    @property
    def soldiers(self):
        return self.camps['blue'].soldiers + self.camps['red'].soldiers

    @property
    def done(self):
        for squad in self.camps.values():
            if squad.commander.tagged:
                return True
        return False

    @property
    def winner(self):
        blue_wins = self.camps['red'].commander.tagged
        red_wins = self.camps['blue'].commander.tagged

        if blue_wins and (not red_wins):
            return 'blue'
        elif (not blue_wins) and red_wins:
            return 'red'
        elif blue_wins and red_wins:
            return 'draw'
        else:
            return None