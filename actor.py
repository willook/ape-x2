import _pickle as pickle
import os
from multiprocessing import Process, Queue
import queue

import zmq
import torch
from tensorboardX import SummaryWriter
import numpy as np
from gym import spaces

import utils
from memory import BatchStorage
from wrapper import make_atari, wrap_atari_dqn
from model import DuelingDQN
from model import RandomPolicy
from model import ActorCritic
from arguments import argparser

from runtag.actions import *
from runtag.envs.centralized import RunTagEnv


def get_environ():
    actor_id = int(os.environ.get('ACTOR_ID', '-1'))
    n_actors = int(os.environ.get('N_ACTORS', '-1'))
    replay_ip = os.environ.get('REPLAY_IP', '-1')
    learner_ip = os.environ.get('LEARNER_IP', '-1')
    assert (actor_id != -1 and n_actors != -1)
    assert (replay_ip != '-1' and learner_ip != '-1')
    return actor_id, n_actors, replay_ip, learner_ip


def connect_param_socket(ctx, param_socket, learner_ip, actor_id):
    socket = ctx.socket(zmq.REQ)
    socket.connect("tcp://{}:52002".format(learner_ip))
    socket.send(pickle.dumps((actor_id, 1)))
    socket.recv()
    param_socket.connect('tcp://{}:52001'.format(learner_ip))
    socket.send(pickle.dumps((actor_id, 2)))
    socket.recv()
    print("Successfully connected to learner!")
    socket.close()


def recv_param(learner_ip, actor_id, param_queue):
    ctx = zmq.Context()
    param_socket = ctx.socket(zmq.SUB)
    param_socket.setsockopt(zmq.SUBSCRIBE, b'')
    param_socket.setsockopt(zmq.CONFLATE, 1)
    connect_param_socket(ctx, param_socket, learner_ip, actor_id)
    while True:
        data = param_socket.recv(copy=False)
        param = pickle.loads(data)
        param_queue.put(param)

class CommanderPolicy():
    def __init__(self, model):
        self.model = model

    def next_action(self, observation, epsilon=0):
        return self.model.act(observation, epsilon)

class SubordinatePolicy():
    def next_action(self, observation):
        direction = RunTagEnv.directions[observation['direction']]
        if direction is None:
            return RunTagEnv.from_subordinate_action(SubordinateListen())
        else:
            return RunTagEnv.from_subordinate_action(SubordinateMove(direction))

def flatten(env, observation):
    observation = torch.as_tensor(spaces.utils.flatten(env.commander_observation_space, observation), dtype=torch.float)
    return torch.reshape(observation, (1, -1))

def exploration(args, actor_id, n_actors, replay_ip, param_queue):
    ctx = zmq.Context()
    batch_socket = ctx.socket(zmq.DEALER)
    batch_socket.setsockopt(zmq.IDENTITY, pickle.dumps('actor-{}'.format(actor_id)))
    batch_socket.connect('tcp://{}:51001'.format(replay_ip))
    outstanding = 0

    writer = SummaryWriter(comment="-{}-actor{}".format(args.env, actor_id))
    
    env = RunTagEnv(width=5, height=5, number_of_subordinates=1, max_steps=1000)

    # env = make_atari(args.env)
    # env = wrap_atari_dqn(env, args)

    seed = args.seed + actor_id
    utils.set_global_seeds(seed, use_torch=True)
    env.seed(seed)

    blue_commander_model = DuelingDQN(env)
    red_commander_model = RandomPolicy(env)

    blue_commander_policy = CommanderPolicy(blue_commander_model)
    red_commander_policy = CommanderPolicy(red_commander_model)
    subordinate_policy = SubordinatePolicy()

    # model = DuelingDQN(env)
    epsilon = args.eps_base ** (1 + actor_id / (n_actors - 1) * args.eps_alpha)
    storage = BatchStorage(args.n_steps, args.gamma)

    param = param_queue.get(block=True)
    blue_commander_model.load_state_dict(param)
    param = None
    print("Received First Parameter!")

    episode_reward, episode_length, episode_idx, actor_idx = 0, 0, 0, 0
    states = env.reset()
    while True:
        #action, q_values = model.act(torch.FloatTensor(np.array(state[0])), epsilon)
        state = flatten(env, states[0])
        blue_com_action, q_values = blue_commander_policy.next_action(state, epsilon)
        blue_sub_action = subordinate_policy.next_action(states[1])
        red_com_action = red_commander_policy.next_action(flatten(env, states[2]))
        red_sub_action = subordinate_policy.next_action(states[3])
        actions = [
                blue_com_action,
                blue_sub_action,
                red_com_action,
                red_sub_action,
            ]


        next_states, rewards, dones, _ = env.step(actions)
        next_state, reward, done, action = next_states[0], rewards[0], dones[0], actions[0]
        # print('state:', state)
        storage.add(state, reward, action, done, q_values)

        states = next_states
        episode_reward += reward
        episode_length += 1
        actor_idx += 1

        if done or episode_length == args.max_episode_length:
            state = env.reset()
            writer.add_scalar("actor/episode_reward", episode_reward, episode_idx)
            writer.add_scalar("actor/episode_length", episode_length, episode_idx)
            episode_reward = 0
            episode_length = 0
            episode_idx += 1

        if actor_idx % args.update_interval == 0:
            try:
                param = param_queue.get(block=False)
                model.load_state_dict(param)
                print("Updated Parameter..")
            except queue.Empty:
                pass

        if len(storage) == args.send_interval:
            batch, prios = storage.make_batch()
            data = pickle.dumps((batch, prios))
            batch, prios = None, None
            storage.reset()
            while outstanding >= args.max_outstanding:
                batch_socket.recv()
                outstanding -= 1
            batch_socket.send(data, copy=False)
            outstanding += 1
            print("Sending Batch..")


def main():
    actor_id, n_actors, replay_ip, learner_ip = get_environ()
    #actor_id, n_actors, replay_ip, learner_ip = 0, 2, '127.0.0.1', '127.0.0.1'
    args = argparser()
    param_queue = Queue(maxsize=3)

    procs = [
        Process(target=exploration, args=(args, actor_id, n_actors, replay_ip, param_queue)),
        Process(target=recv_param, args=(learner_ip, actor_id, param_queue)),
    ]

    for p in procs:
        p.start()
    for p in procs:
        p.join()
    return True


if __name__ == '__main__':
    os.environ["OMP_NUM_THREADS"] = "1"
    main()
