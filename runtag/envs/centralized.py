import gym
import numpy as np
from gym import spaces
from gym.utils import seeding
from runtag.actions import *
from runtag.entities import Commander, Subordinate
from runtag.game import Game
from runtag.renderer import TextRenderer
from runtag.station import Station
from runtag.utils import l1_distance


class RunTagEnv(gym.Env):
    camps = ['blue', 'red']
    directions = [None, 'up', 'left', 'down', 'right']

    def __init__(self, width, height, number_of_subordinates, max_steps=None):
        self.width, self.height = width, height
        self.number_of_subordinates = number_of_subordinates
        self.max_steps = max_steps

        self.number_of_agents_per_camp = (1 + number_of_subordinates)
        self.number_of_agents = len(self.camps) * self.number_of_agents_per_camp

        self.commander_action_space = spaces.Discrete(
            1 # observe
            + len(self.directions) # (no-op, up, left, down, right)
            + (number_of_subordinates * len(self.directions))) # command subordinate i, (no-op, up, left, down, right)
        self.subordinate_action_space = spaces.Discrete(
            1 # listen
            + len(self.directions)) # (no-op, up, left, down, right)

        self.commander_observation_space = spaces.Dict({
            'squad': spaces.Discrete(len(self.camps)),
            'position': spaces.MultiDiscrete([width, height]),
            'commanders': spaces.Box(low=-1, high=1,
                                     shape=(height, width), dtype=np.int8),
            'subordinates': spaces.Box(low=-1, high=1,
                                       shape=(height, width), dtype=np.int8),
        })
        self.subordinate_observation_space = spaces.Dict({
            'squad': spaces.Discrete(len(self.camps)),
            'identifier': spaces.Discrete(number_of_subordinates),
            'direction': spaces.Discrete(len(self.directions)),
        })

        self.seed()

    def reset(self):
        self.game = Game.make(self.width, self.height, self.number_of_subordinates)
        self.grid = self.game.grid

        self.renderer = TextRenderer(self.game)
        self.steps = 0

        return self.get_observations()

    def render(self, mode=None):
        self.renderer.render()

    def step(self, actions):
        assert len(actions) == self.number_of_agents

        if (self.max_steps is not None) and (self.steps >= self.max_steps):
            return [
                self.get_observations(),
                self.calculate_rewards(),
                [True] * len(actions),
                dict(exceeded=True),
            ]

        for index_of_camp, squad in enumerate(self.game.camps.values()):
            index = index_of_camp * self.number_of_agents_per_camp
            self.commander_action_of(actions[index]).act(squad.commander)

        for index_of_camp, squad in enumerate(self.game.camps.values()):
            for index_of_subordinate, subordinate in enumerate(squad.subordinates):
                index = index_of_camp * self.number_of_agents_per_camp + index_of_subordinate + 1
                self.subordinate_action_of(actions[index]).act(subordinate)

        self.steps += 1
        return [
            self.get_observations(),
            self.calculate_rewards(),
            [self.game.done] * len(actions),
            dict(),
        ]

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def calculate_rewards(self):
        rewards = []

        for squad in self.game.camps.values():
            commander = squad.commander
            rewards.append(self.calculate_commander_reward(squad.commander))

            for subordinate in squad.subordinates:
                rewards.append(self.calculate_subordinate_reward(subordinate))

        return rewards

    def calculate_commander_reward(self, commander):
        return -sum(l1_distance(self.grid.position_of(commander),
                                self.grid.position_of(entity))
                    for entity in self.game.entities(Subordinate)
                    if commander.is_enemy(entity))

    def calculate_subordinate_reward(self, subordinate):
        return -sum(l1_distance(self.grid.position_of(subordinate),
                                self.grid.position_of(entity))
                    for entity in self.game.entities(Commander)
                    if subordinate.is_enemy(entity))

    def get_observations(self):
        observations = []

        for squad in self.game.camps.values():
            observations.append(self.get_commander_observation(squad.commander))

            for subordinate in squad.subordinates:
                observations.append(self.get_subordinate_observation(subordinate))

        return observations

    def get_commander_observation(self, commander):
        position = (0, 0)
        commanders = np.zeros((self.height, self.width), dtype=np.int8)
        subordinates = np.zeros((self.height, self.width), dtype=np.int8)

        if commander.position is not None:
            position = commander.position

        if commander.observation is not None:
            for (x, y), entities in commander.observation.items():
                for entity in entities:
                    if entity.rank == 'commander':
                        commanders[y][x] = +1 if commander.is_friendly(entity) else -1
                    elif entity.rank == 'subordinate':
                        subordinates[y][x] = +1 if commander.is_friendly(entity) else -1

        return {
            'squad': self.camps.index(commander.squad.name),
            'position': np.array(position, dtype=np.int8),
            'commanders': commanders,
            'subordinates': subordinates,
        }

    def get_subordinate_observation(self, subordinate):
        direction = 0
        if subordinate.direction is not None:
            direction = self.directions.index(subordinate.direction)

        return {
            'squad': self.camps.index(subordinate.squad.name),
            'identifier': subordinate.identifier,
            'direction': direction,
        }

    @classmethod
    def commander_action_of(cls, action):
        if action == 0:
            return CommanderObserve()
        elif 1 <= action <= len(cls.directions):
            return CommanderMove(cls.directions[action - 1])
        else:
            index = action - 1 - len(cls.directions)
            target = index // len(cls.directions)
            return CommanderCommand(target, cls.directions[index - (target * len(cls.directions))])

    @classmethod
    def subordinate_action_of(cls, action):
        if action == 0:
            return SubordinateListen()
        elif 1 <= action <= len(cls.directions):
            return SubordinateMove(cls.directions[action - 1])

    @classmethod
    def from_commander_action(cls, action):
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

    @classmethod
    def from_subordinate_action(cls, action):
        if isinstance(action, SubordinateListen):
            return 0
        elif isinstance(action, SubordinateMove):
            return 1 + cls.directions.index(action.direction)
