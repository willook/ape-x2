from collections import OrderedDict

from .entities import Commander, Subordinate
from .types import Position, as_position


class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.tiles = {
            Position(x, y): set()
            for x in range(width) for y in range(height)
        }
        self.entities = OrderedDict()

    def add(self, position, entity):
        position = as_position(position)

        if self.entity_exists(entity):
            raise ValueError('entity is already added in the grid')

        if not self.within_grid(position):
            raise ValueError('position is out of the grid')

        self.tiles[position].add(entity)
        self.entities[entity] = position

    def move(self, entity, direction):
        if not self.entity_exists(entity):
            raise ValueError('entity is not in the grid')

        position = self.position_of(entity)
        next_position = getattr(position, direction)().clip(self.width, self.height)

        self.tiles[position].remove(entity)
        self.tiles[next_position].add(entity)
        self.entities[entity] = next_position

    def entity_exists(self, entity):
        return entity in self.entities

    def within_grid(self, position):
        position = as_position(position)
        return ((0 <= position.x < self.width) and (0 <= position.y < self.height))

    def entities_at(self, position):
        if not self.within_grid(position):
            raise ValueError('position is out of the grid')
        return list(self.tiles[position])

    def entities_with(self, entity):
        return self.entities_at(self.position_of(entity))

    def position_of(self, entity):
        if not self.entity_exists(entity):
            raise ValueError('entity is not in the grid')
        return self.entities[entity]

    def __getitem__(self, position):
        return self.entities_at(position)