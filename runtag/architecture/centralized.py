from runtag.actions import *
from runtag.architecture import BaseRunTag
from runtag.station import Station
from runtag.utils import prompt


class RunTag(BaseRunTag):
    wasd_to_direction = {
        'w': 'up',
        'a': 'left',
        's': 'down',
        'd': 'right',
    }

    def __init__(self, game, on_tick=None):
        super().__init__(game, on_tick)
        self.steps = 0

    def run(self):
        while not self.game.done:
            self.tick()

            if self.on_tick is not None:
                self.on_tick(self.game)

            self.steps += 1

    def tick(self):
        for camp in ['blue', 'red']:
            squad = self.game.camps[camp]
            commander = squad.commander

            if (self.steps % 3) == 0:
                CommanderObserve().act(commander)
                input(f'{camp}.commander observes')
            elif (self.steps % 3) == 1:
                commander_direction = self.wasd_to_direction[prompt(f'{camp}.commander moves', 'wasd')]
                CommanderMove(commander_direction).act(commander)
            elif (self.steps % 3) == 2:
                subordinate_identifier = prompt(f'{camp}.commander commands subordinate',
                                                ''.join(map(str, range(len(squad.subordinates)))))
                subordinate_direction = self.wasd_to_direction[prompt(f'  to move', 'wasd')]
                CommanderCommand(int(subordinate_identifier), subordinate_direction).act(commander)

        for camp in ['blue', 'red']:
            squad = self.game.camps[camp]

            for subordinate in squad.subordinates:
                if (self.steps % 2)== 0:
                    direction = SubordinateListen().act(subordinate)
                    input(f'{camp}.subordinate#{subordinate.identifier} receives to move {direction}')
                elif (self.steps % 2)== 1:
                    input(f'{camp}.subordinate#{subordinate.identifier} moves {subordinate.direction}')
                    SubordinateMove(subordinate.direction).act(subordinate)