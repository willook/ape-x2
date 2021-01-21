import asyncio

import zmq
import zmq.asyncio
from runtag.actions import *
from runtag.architecture import BaseRunTag
from runtag.station import Station


class Room:
    context = zmq.asyncio.Context()

    def __init__(self, game):
        self.game = game
        self.index_identity = [None] * len(self.game.soldiers)
        self.identity_index = dict()

    async def gather(self, address):
        self.prepare_socket(address)

        while not self.ready:
            identity = await self.socket.recv()
            affiliation = await self.socket.recv_pyobj()

            index = self.assign_index(affiliation)
            self.index_identity[index] = identity
            self.identity_index[identity] = index

            await self.socket.send(identity, flags=zmq.SNDMORE)
            await self.socket.send_pyobj(index)
            print(f'- {affiliation["camp"]}.{affiliation["rank"]}@{index} connected')

        for identity in self.index_identity:
            await self.socket.send(identity, flags=zmq.SNDMORE)
            await self.socket.send_pyobj(self.game)

    def prepare_socket(self, address):
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(address)

    @property
    def ready(self):
        return all(map(bool, self.index_identity))

    def assign_index(self, affiliation):
        is_camp_blue = affiliation['camp'] == 'blue'
        is_commander = affiliation['rank'] == 'commander'

        begin, end = 0, len(self.game.soldiers) // 2
        if not is_camp_blue:
            begin, end = end, len(self.game.soldiers)

        if is_commander:
            index = begin
            if self.index_identity[index] is not None:
                raise ValueError(f'{affiliation["camp"]}.commander is already joined')
        else:
            for index in range(begin + 1, end):
                if self.index_identity[index] is None:
                    break
            else:
                raise ValueError(f'All {affiliation["camp"]}.subordinates are already joined')
        return index


class RunTag(BaseRunTag):
    def __init__(self, game, on_tick=None):
        super().__init__(game, on_tick)
        self.room = Room(self.game)
        self.steps = 0

    async def run(self, address):
        print('Waiting for agents...')
        await self.room.gather(address)

        print('Starting game...')
        while not self.game.done:
            await self.tick()
            self.steps += 1

    async def tick(self):
        identity = await self.socket.recv()
        message = await self.socket.recv_pyobj()

        soldier = self.soldier_of(identity)
        action_factory = getattr(self, f'make_{soldier.rank}_{message["action"]}')
        action = action_factory(*message.get('parameters', []))
        action.act(soldier)

        await self.socket.send(identity, flags=zmq.SNDMORE)
        await self.socket.send_pyobj(self.game)

        if self.on_tick is not None:
            self.on_tick(self.game, self.soldier_of(identity), action)

    def make_commander_observe(self):
        return CommanderObserve()

    def make_commander_move(self, direction):
        return CommanderMove(direction)

    def make_commander_command(self, subordinate, direction):
        return CommanderCommand(subordinate, direction)

    def make_subordinate_listen(self):
        return SubordinateListen()

    def make_subordinate_move(self, direction):
        return SubordinateMove(direction)

    @property
    def socket(self):
        return self.room.socket

    def soldier_of(self, identity):
        return self.game.soldiers[self.room.identity_index[identity]]