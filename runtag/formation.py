import random
import math

from itertools import product
from .types import Position


class Formation:
    def __init__(self, grid):
        self.grid = grid

    def place(self, number_of_camps, number_of_soldiers):
        camp_positions = self.place_camps(number_of_camps)

        for camp_position in camp_positions:
            yield self.place_squad(camp_position, number_of_soldiers)

    def place_camps(self, number_of_camps):
        assert 0 <= number_of_camps <= 4
        verticies = [
            Position(x=0, y=0), Position(x=self.grid.width - 1, y=0),
            Position(x=0, y=self.grid.height - 1), Position(x=self.grid.width - 1, y=self.grid.height - 1),
        ]

        return random.sample(verticies, number_of_camps)

    def place_squad(self, camp_position, number_of_soldiers):
        radius = math.ceil(math.sqrt(2 * number_of_soldiers))

        x0, y0 = camp_position
        x1, y1 = Position(x=x0 + ((+1 if x0 == 0 else -1) * (radius - 1)),
                          y=y0 + ((+1 if y0 == 0 else -1) * (radius - 1)))

        left, right = (x0, x1) if x0 == 0 else (x1, x0)
        top, bottom = (y0, y1) if y0 == 0 else (y1, y0)

        candidates = list(product(range(left, right + 1), range(top, bottom + 1)))
        return random.sample(candidates, number_of_soldiers)