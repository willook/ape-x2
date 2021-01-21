from collections import namedtuple
from datetime import datetime


Message = namedtuple('Message', ['sender', 'payload', 'receiver'])


class Envelope:
    def __init__(self, message, timeout=5):
        self.message = message
        self.sent_at = datetime.now()
        self.timeout = timeout

    @property
    def sender(self):
        return self.message.sender

    @property
    def receiver(self):
        return self.message.receiver

    @property
    def expired(self):
        return (datetime.now() - self.sent_at).total_seconds() >= self.timeout


class Station:
    stations = dict()

    def __init__(self, channel):
        self.channel = channel
        self.envelopes = set()

    @classmethod
    def of(cls, channel):
        if channel not in cls.stations:
            cls.stations[channel] = Station(channel)
        return cls.stations[channel]

    @classmethod
    def all(cls):
        return list(cls.stations.values())

    def send(self, sender, payload, receiver):
        self.discard_expirations()
        self.envelopes.add(Envelope(Message(sender, payload, receiver)))

    def receive(self, sender, receiver, count=0):
        self.discard_expirations()

        all_senders = sender is None
        all_receivers = receiver is None

        received = set()
        for envelope in self.envelopes:
            if (not all_senders) and (envelope.sender is not sender):
                continue
            if (not all_receivers) and (envelope.receiver is not receiver):
                continue
            received.add(envelope)

            if (count > 0) and (len(received) >= count):
                break

        self.envelopes -= received
        return [envelope.message._asdict() for envelope in received]

    def discard_expirations(self):
        expired = {envelope for envelope in self.envelopes if envelope.expired}
        self.envelopes -= expired