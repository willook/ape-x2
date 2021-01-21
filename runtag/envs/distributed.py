import asyncio

import gym
import numpy as np
import zmq
from gym import spaces
from gym.utils import seeding
from runtag.actions import *
from runtag.entities import Commander, Subordinate
from runtag.renderer import TextRenderer
from runtag.utils import l1_distance


class SoldierEnv(gym.Env):
    context = zmq.Context()

    rank = None
    directions = [None, 'up', 'left', 'down', 'right']

    def __init__(self, address, camp):
        self.address = address
        self.camp = camp

        self.action_space = None
        self.observation_space = None
        self.seed()

    def reset(self):
        self.prepare_socket(self.address)
        self.join()

        return self.get_observation()

    def render(self, mode=None):
        TextRenderer(self.game).render()

    def step(self, action):
        self.socket.send_pyobj(self.message_of(action))
        self.game = self.socket.recv_pyobj()

        return [self.get_observation(),
                self.calculate_reward(),
                self.game.done,
                dict()]

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def prepare_socket(self, address):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.address)

    def join(self):
        self.socket.send_pyobj({'camp': self.camp, 'rank': self.rank})
        self.index = self.socket.recv_pyobj()

        self.game = self.socket.recv_pyobj()
        self.camp_index = list(self.game.camps.keys()).index(self.camp)

    def get_observation(self):
        raise NotImplementedError()

    @classmethod
    def message_of(cls, action):
        raise NotImplementedError()

    def calculate_reward(self):
        raise NotImplementedError()

    @classmethod
    def from_action(cls, action):
        raise NotImplementedError()

    @property
    def grid(self):
        return self.game.grid

    @property
    def squad(self):
        return self.game.camps[self.camp]

    @property
    def soldier(self):
        return self.game.soldiers[self.index]


class CommanderEnv(SoldierEnv):
    rank = 'commander'

    def reset(self):
        observation = super().reset()

        self.action_space = spaces.Discrete(
            1 # observe
            + len(self.directions) # (no-op, up, left, down, right)
            + (len(self.squad.subordinates) * len(self.directions))) # command subordinate i, (no-op, up, left, down, right)
        self.observation_space = spaces.Dict({
            'camp': spaces.Discrete(len(self.game.camps)),
            'position': spaces.MultiDiscrete([self.grid.width, self.grid.height]),
            'commanders': spaces.Box(
                low=-1, high=1, # -1 indicates enemy, +1 indicates friendly
                shape=(self.grid.height, self.grid.width),
                dtype=np.int8),
            'subordinates': spaces.Box(
                low=-1, high=1,  # -1 indicates enemy, +1 indicates friendly
                shape=(self.grid.height, self.grid.width),
                dtype=np.int8)})

        return observation

    def get_observation(self):
        position = (0, 0)
        commanders = np.zeros((self.grid.height, self.grid.width), dtype=np.int8)
        subordinates = np.zeros((self.grid.height, self.grid.width), dtype=np.int8)

        if self.soldier.position is not None:
            position = self.soldier.position

        if self.soldier.observation is not None:
            for (x, y), entities in self.soldier.observation.items():
                for entity in entities:
                    if entity.rank == 'commander':
                        commanders[y][x] = +1 if self.soldier.is_friendly(entity) else -1
                    elif entity.rank == 'subordinate':
                        subordinates[y][x] = +1 if self.soldier.is_friendly(entity) else -1

        return {'camp': self.camp_index,
                'position': np.array(position, dtype=np.int8),
                'commanders': commanders,
                'subordinates': subordinates}

    @classmethod
    def message_of(cls, action):
        if action == 0:
            return {'action': 'observe'}
        elif 1 <= action <= len(cls.directions):
            return {'action': 'move',
                    'parameters': [cls.directions[action - 1]]}
        else:
            index = action - 1 - len(cls.directions)
            target = index // len(cls.directions)
            direction = cls.directions[index - (target * len(cls.directions))]
            return {'action': 'command',
                    'parameters': [target, direction]}

    def calculate_reward(self):
        return -sum(l1_distance(self.grid.position_of(self.soldier),
                                self.grid.position_of(entity))
                    for entity in self.game.entities(Subordinate)
                    if self.soldier.is_enemy(entity))

    @classmethod
    def from_action(cls, action):
        if isinstance(action, CommanderObserve):
            return 0
        elif isinstance(action, CommanderMove):
            return 1 + cls.directions.index(action.direction)
        elif isinstance(action, CommanderCommand):
            subordinate = action.subordinate
            identifier = subordinate.identifier if isinstance(subordinate, Subordinate) \
                         else subordinate
            return 1 + len(cls.directions) \
                   + identifier * len(cls.directions) \
                   + cls.directions.index(action.direction)


class SubordinateEnv(SoldierEnv):
    rank = 'subordinate'

    def __init__(self, address, camp):
        super().__init__(address, camp)

    def reset(self):
        super().reset()

        self.action_space = spaces.Discrete(
            1 # listen
            + len(self.directions)) # (no-op, up, left, down, right)

        self.observation_space = spaces.Dict({
            'camp': spaces.Discrete(len(self.game.camps)),
            'identifier': spaces.Discrete(len(self.squad.subordinates)),
            'direction': spaces.Discrete(len(self.directions))})
        self.seed()

    def get_observation(self):
        direction = 0

        if self.soldier.direction is not None:
            direction = self.directions.index(self.soldier.direction)

        return {'camp': self.camp_index,
                'identifier': self.soldier.identifier,
                'direction': direction}

    @classmethod
    def message_of(cls, action):
        if action == 0:
            return {'action': 'listen'}
        elif 1 <= action <= len(cls.directions):
            return {'action': 'move',
                    'parameters': [cls.directions[action - 1]]}

    def calculate_reward(self):
        return -sum(l1_distance(self.grid.position_of(self.soldier),
                                self.grid.position_of(entity))
                    for entity in self.game.entities(Commander)
                    if self.soldier.is_enemy(entity))

    @classmethod
    def from_action(cls, action):
        if isinstance(action, SubordinateListen):
            return 0
        elif isinstance(action, SubordinateMove):
            return 1 + cls.directions.index(action.direction)
