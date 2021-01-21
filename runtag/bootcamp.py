from .entities import Commander, Subordinate, Squad


class Bootcamp:
    def __init__(self, grid):
        self.grid = grid

    def recruit(self, name, number_of_subordinates=1):
        squad = Squad(self.grid, name)

        squad.assign(Commander(self.grid))
        for index in range(number_of_subordinates):
            squad.assign(Subordinate(self.grid, identifier=index))

        return squad