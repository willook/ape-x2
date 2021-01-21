from collections import namedtuple


def as_position(value):
    if isinstance(value, Position):
        return value
    elif isinstance(value, (int, float)):
        return Position(value, value)
    elif type(value) is tuple:
        return Position._make(value)
    return None


class Position(namedtuple('Position', ['x', 'y'])):
    def up(self):
        return self + Position(0, -1)

    def down(self):
        return self + Position(0, +1)

    def left(self):
        return self + Position(-1, 0)

    def right(self):
        return self + Position(+1, 0)

    def clip(self, width, height):
        return Position(x=max(0, min(self.x, width - 1)),
                        y=max(0, min(self.y, height - 1)))

    def in_line(self, other):
        return (self.x == other.x) or (self.y == other.y)

    def __add__(self, other):
        other = as_position(other)
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        other = as_position(other)
        return Position(self.x - other.x, self.y - other.y)

    def __truediv__(self, other):
        other = as_position(other)
        return Position(self.x / other.x, self.y / other.y)


class Entity:
    def __init__(self, grid):
        self.grid = grid

    def __repr__(self):
        return f'{type(self).__name__}@0x{id(self):x}'


class Equipment(Entity):
    def __init__(self, grid, owner):
        super().__init__(grid)

        assert isinstance(owner, Entity)
        self.owner = owner

    def operate(self, *args, **kwargs):
        raise NotImplementedError()