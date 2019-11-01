#! python3
"""
Modeling of the Channel.
This include a the sending delay, and transmission delay
"""
from abc import ABC, abstractmethod
from time import time


class Channel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def send_frames(self, frames):
        """Sends data to the channel.
        Return time it took to tranfer the data.
        """


class StableChannelNoWindow(Channel):
    "Very Simple channel modulation where tansport layer is not modeled"
    def __init__(self, bandwith, sending_delay=0, speed=1):
        self.bandwith = bandwith
        self.sending_delay = sending_delay
        self.speed = speed

    def send_frames(self, frames):
        """update availability field of Frames
        Return list of time that
        """
        for f in frames:
            f.availability = time() * self.speed + f.size / self.bandwith + self.sending_delay

    def changeBandwith(self, bandwith):
        self.bandwith = bandwith


class StableChannelWindow(Channel):
    "Very Simple channel modulation where tansport layer is not modeled"
    def __init__(self, bandwith, sending_delay=0):
        self.bandwith = bandwith
        self.sending_delay = sending_delay

    def send_frames(self, frames):
        """update availability field of Frames
        Return list of time that
        """
        for f in frames:
            f.availability = time() + f.size / self.bandwith + self.sending_delay

    def changeBandwith(self, bandwith):
        self.bandwith = bandwith


# Maybe to simulate the window consider the length of frames
