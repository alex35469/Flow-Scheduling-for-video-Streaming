#! python3
"""
Modeling of the Channel.
This include a the sending delay, and transmission delay
"""
from abc import ABC, abstractmethod
from time import time

class Channel(ABC):
    def __init__(self, channelDesc):
        self.channelDesc = channelDesc

    @abstractmethod
    def send_frames(self, frames):
        """Sends data to the channel.
        Return time it took to tranfer the data.
        """


class StableChannelNoWindow(Channel):
    def __init__(self, bandwith, sending_delay=0):
        self.bandwith = bandwith
        self.sending_delay = sending_delay

        def delay(size):
            return size / self.bandwith

        super().__init__(delay)

    def send(self, size):
        return self.channelDesc(size)

    def send_frames(self, frames):
        """update availability field of Frames
        Return list of time that
        """
        for f in frames:
            self.send(f.size)
            f.availability = time() + self.send(f.size) + self.sending_delay

    def changeBandwith(bandwith):
        self.bandwith = bandwith

# Maybe to simulate the window consider the length of frames
