import colorful as cf
from pprint import pprint
from itertools import chain

class Renderer:
    def __init__(self, game):
        self.game = game
        self.grid = game.grid

    def render(self):
        raise NotImplementedError()

class TextRenderer(Renderer):
    def __init__(self, game):
        super().__init__(game)
        self.number_of_soldiers = len(self.game.soldiers) // 2
        self.tile_width = (3 * self.number_of_soldiers) + (self.number_of_soldiers - 1)

    def render(self, camp=None, observation_only=False):
        tiles = [[self.make_tile() for _ in range(self.grid.width)]
                                   for _ in range(self.grid.height)]

        soldiers = set()
        if observation_only:
            camps = self.game.camps.values() if camp is None else [self.game.camps[camp]]
            for squad in camps:
                has_observed = squad.commander.observation is not None
                soldiers.add(squad.commander)
                soldiers.update(chain.from_iterable(
                    squad.commander.observation.values()) if has_observed
                    else {})
        else:
            soldiers.update(self.grid.entities.keys())

        for soldier in soldiers:
            x, y = self.grid.position_of(soldier)
            i, j = self.index_of(soldier)
            tiles[x][y][i][j] = self.id_of(soldier)

        self.print_x_axis(end='\n')

        for y in range(self.grid.height):
            self.put(' ')
            self.print_tile_border(end='\n')

            self.print_tile_top(tiles, y, end='\n')
            self.print_tile_bottom(tiles, y, end='\n')

        self.put(' ')
        self.print_tile_border(end='\n')

    def id_of(self, soldier):
        return f'{soldier.squad.name[0].upper()}' \
               f'{soldier.rank[0].upper()}' \
               f'{soldier.identifier if soldier.rank == "subordinate" else " "}'

    def index_of(self, soldier):
        return (
            0 if soldier.squad is self.game.camps['blue'] else 1,
            0 if soldier.rank == 'commander' else 1 + soldier.identifier,
        )

    def make_tile(self):
        number_of_soldiers = len(self.game.camps['blue'].soldiers)
        return [[' ' * 3] * number_of_soldiers for _ in range(number_of_soldiers)]

    def print_x_axis(self, end=''):
        self.put(' ')
        for x in range(self.grid.width):
            self.put(f' {x:<{self.tile_width}}')
        self.put(end)

    def print_tile_border(self, end=''):
        self.put('+')
        for x in range(self.grid.width):
            self.put(f'{"-" * self.tile_width}+')
        self.put(end)

    def print_tile_top(self, tiles, y, end=''):
        self.put(f'{y}|')
        for x in range(self.grid.width):
            for i in range(self.number_of_soldiers - 1):
                self.put(tiles[x][y][0][i], end=' ')
            self.put(tiles[x][y][0][self.number_of_soldiers - 1], end='|')
        self.put(end)

    def print_tile_bottom(self, tiles, y, end=''):
        self.put(' |')
        for x in range(self.grid.width):
            for i in range(self.number_of_soldiers - 1):
                self.put(tiles[x][y][1][i], end=' ')
            self.put(tiles[x][y][1][self.number_of_soldiers - 1], end='|')
        self.put(end)

    def put(self, *args, **kwargs):
        if 'end' not in kwargs:
            kwargs['end'] = ''
        print(*args, **kwargs)