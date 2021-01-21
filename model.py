"""
Module for DQN Model in Ape-X.
"""
import random
import torch
import torch.nn as nn
from gym import spaces


class ActorCritic(nn.Module):
    
    def __init__(self, env):
        super(DQN, self).__init__()

        self.input_Shape = env.commander_observation_space.shape
        self.num_actions = env.commander_action_space.shape

        self.flatten = Flatten()

        self.critic = nn.Sequential(
                nn.Linear(self.input_shape, 256),
                nn.ReLU(),
                nn.Linear(256, 1)
        )
        
        self.actor = nn.Sequential(
                nn.Linear(self.input_shape, 256),
                nn.ReLU(),
                nn.Linear(256, self.num_actions),
                nn.Softmax(dim=1)
        )


    def forward(self, x):
        value = self.critic(x)
        probs = self.actor(x)
        dist = Categorical(probs)
        return dist, value

class RandomPolicy():
    def __init__(self, env):
        self.num_actions = spaces.utils.flatdim(env.commander_action_space)

    def act(self, state, epsilon):
        action = random.randrange(self.num_actions)
        return action


class DuelingDQN(nn.Module):
    """
    Dueling Network Architectures for Deep Reinforcement Learning
    https://arxiv.org/abs/1511.06581
    """
    def __init__(self, env):
        super(DuelingDQN, self).__init__()

        self.observation_size = spaces.utils.flatdim(env.commander_observation_space)
        print('obs size:', self.observation_size)
        self.num_actions = spaces.utils.flatdim(env.commander_action_space)
        print('act size:', self.num_actions)

        self.flatten = Flatten()

        self.advantage = nn.Sequential(
            init(nn.Linear(self.observation_size, 512)),
            nn.ReLU(),
            init(nn.Linear(512, self.num_actions))
        )

        self.value = nn.Sequential(
            init(nn.Linear(self.observation_size, 512)),
            nn.ReLU(),
            init(nn.Linear(512, 1))
        )

    def forward(self, x):
        advantage = self.advantage(x)
        value = self.value(x)
        return value + advantage - advantage.mean(0, keepdim=True)

    def _feature_size(self):
        return self.features(torch.zeros(1, *self.input_shape)).view(1, -1).size(1)

    def act(self, state, epsilon):
        """
        Return action, max_q_value for given state
        """
        with torch.no_grad():
            state = state.squeeze(0)
            q_values = self.forward(state)
            #print('q values:', q_values)
            #print('q values shape:', q_values.shape)

            if random.random() > epsilon:
                #print('q_max:', q_values.max(0))
                #print('action:', q_values.max(0)[1].item())
                action = q_values.max(0)[1].item()
            else:
                action = random.randrange(self.num_actions)
        return action, q_values.numpy()


class Flatten(nn.Module):
    """
    Simple module for flattening parameters
    """
    def forward(self, x):
        return x.view(x.size(0), -1)


def init_(module, weight_init, bias_init, gain=1):
    weight_init(module.weight.data, gain=gain)
    bias_init(module.bias.data)
    return module


def init(module):
    return init_(module,
                 nn.init.orthogonal_,
                 lambda x: nn.init.constant_(x, 0),
                 nn.init.calculate_gain('relu'))
