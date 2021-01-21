from .types import Equipment, Position
from .station import Message, Station


class Compass(Equipment):
    def operate(self, *args, **kwargs):
        return self.grid.position_of(self.owner)


class Telescope(Equipment):
    def operate(self, *args, **kwargs):
        return dict(self.observe())

    def positions(self):
        me = self.grid.position_of(self.owner)
        return [Position(x, me.y) for x in range(self.grid.width)] \
                + [Position(me.x, y) for y in range(self.grid.height)]

    def observe(self):
        for position in self.positions():
            entities = [entity for entity in self.grid[position] if entity is not self]
            if entities:
                yield (position, entities)


class Radio(Equipment):
    def operate(self, receiver=None, payload=None):
        assert self.owner.squad is not None

        if receiver is not None:
            self.talk(receiver, payload)
        else:
            return self.listen()

    def talk(self, receiver, payload):
        self.station.send(self.owner, payload, receiver)

    def listen(self):
        messages = self.station.receive(sender=None, receiver=self.owner, count=1)
        return [message['payload'] for message in messages]

    @property
    def station(self):
        return Station.of(self.channel)

    @property
    def channel(self):
        return self.owner.squad.name