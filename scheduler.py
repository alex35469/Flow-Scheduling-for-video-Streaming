"""
Emulate a simulator for flow scheduling in multiparty live streaming

"""
from abc import ABC, abstractmethod
from stream import Streamer
import numpy as np
import random


class Scheduler(ABC):
    """The scheduler possesses all the queues and has to make a decision: which
    queue he has to pick at which quality"""

    def __init__(self, streamers, dprint=True):

        for streamer in streamers:
            assert(isinstance(streamer, Streamer))
        super().__init__()
        self.streamers = streamers
        self.dprint = dprint

    def __get_poisson_expected_number_of_occurrences(self, streamer, time_elapsed):
        """compute the poisson arrival rate according to the arrival rate in KBps of the source,
        the time elapsed and the mean size of frames of the maximum best quality flow"""
        nb_occ = streamer.arrival_rate*time_elapsed / streamer.mean_frames[-1]
        return nb_occ

    def step(self, describe=False):
        """Do one iteration step: select which queue to pick in, how many packets
         and updates the queues"""
        self.decide()
        self.update()

    def update(self, tstart, tstop):
        """Update all queue with there respective poisson arrival rate.
        If total_bandwith is not 0, adapt the total bandwith used for dynamic
        adaptive bandwith.

        If only total upload bandwith is 0,
        total_upload_bandwith in kbps
        elapsed in sec
        """
        elapsed = tstop - tstart
        assert(elapsed > 0)
        # Compute each time the total incoming flow in case we want to simulate
        # arrival rate change overtime
        lambdas = [self.__get_poisson_expected_number_of_occurrences(s, elapsed)
                   for s in self.streamers]

        def time_occurance():
            return tstart + random.random() * elapsed

        arrivals = [np.random.poisson(l) for l in lambdas]
        time_stamp_separation = [time_occurance() for i in range(sum(arrivals))]
        time_stamp_separation = [(i, t) for i, t in enumerate(sorted(time_stamp_separation))]
        # Spread the arrivals on the time spectrum

        random.shuffle(time_stamp_separation)
        tmp = 0
        updated_frames = []
        for streamer, arrival in zip(self.streamers, arrivals):
            if arrival == 0:
                continue
            new_frames = streamer.update(sorted(time_stamp_separation[tmp: tmp + arrival]))
            updated_frames.extend(new_frames)
            tmp += arrival
        Streamer.Frame_Arrival += sum(arrivals)
        return updated_frames

    def describe(self, full=False):
        s = "Scheduler Description:"
        for streamer in self.streamers:
            s += "\n" + streamer.describe(full) + '\n'
        return s

    @abstractmethod
    def decide(self):
        """Core implementation of the scheduler.

        Return the decided frames
        """


class RandomScheduler(Scheduler):
    """Scheduler that decides randomly which streamers to send the frame from, at
    which quality."""

    def __init__(self, streames):
        super().__init__(streames)

    def decide(self, dprint=False):
        non_empty_flow = [streamer for streamer in
                          self.streamers if not streamer.isEmpty()]
        # No frames in queues
        if len(non_empty_flow) == 0:
            return False

        dStreamer = random.sample(non_empty_flow, 1)[0]
        dQueue = random.randint(0, len(dStreamer.queues) - 1)
        dNbFrames = random.randint(1, dStreamer.queues[dQueue].length)
        decidedFrames = dStreamer.dequeue(dQueue, dNbFrames)

        if decidedFrames and dprint:
            print("Scheduler decided:")
            for f in decidedFrames:
                print(f.describe(True))
        return decidedFrames
