"""
Emulation of the receiver that will consume de stream.
Contains:
"""
from stream import Queue
from time import time


class Receiver:
    """Represents the receiver. """

    MAX_BUFFER = 1_000_000  # Buffer size in KB

    def __init__(self, queues, fps):
        self.queues = queues
        self.fps = fps
        self.lastPlay = [0]*len(queues)  # time of the begining of the last frame played
        self.originQueueDict = dict([(q.name, i) for i, q in enumerate(queues)])
        self.isPlaying = [False] * len(queues)
        self.started = False
        self.startPlay = -1


    def playback(self):
        """Play the frames in the queues independently overtime,
        i.e. at the end of the simulation

        pros: no time consumption during simulation
        cons: Rewards only come at the end (of the playing)

        Return:
        dictionary-like results

        {queue 1 :  total_delay
                    total_rebuffering
                    average_rate
                    total_frame
        queue 2  :  ....       }

        """

        results = {}
        frame_slot = 1 / self.fps

        for q in self.queues:
            # Queue output
            average_rate = 0
            total_rebuffering_time = 0
            total_rebuffering_event = 0
            total_delay = 0
            total_frame = 0

            # State of the queue
            lastPlay = self.lastPlay[self.originQueueDict[q.name]]

            for f in q.queue:

                rebuffering_time = f.availability - lastPlay
                # We have a rebuffering event
                if rebuffering_time > 0:

                    # fast forward to the begining of the playing frame
                    lastPlay = f.availability
                    total_rebuffering_time += rebuffering_time
                    total_rebuffering_event += 1

                total_delay = lastPlay - f.timestamp
                average_rate += f.bitrate
                total_frame += 1
                # fast forward to the end of the playing frame
                lastPlay += frame_slot

            q.flush()

            if total_frame == 0:
                return 0

            self.lastPlay[self.originQueueDict[q.name]] = lastPlay
            results[q.name] = {"total_rebuffering_event": total_rebuffering_event,
                               "total_rebuffering_time": total_rebuffering_time,
                               "total_delay": total_delay,
                               "average_rate": average_rate / total_frame,
                               "total_frame": total_frame}
        return results

    def start(self):
        """Inititate the playing process"""
        self.lastPlay = [time()] * len(self.queues)
        self.startPlay = self.lastPlay[-1]

    def receive(self, frames):
        for frame in frames:
            queue_nb = self.originQueueDict.get(frame.origin)
            if type(queue_nb) is int:
                self.queues[queue_nb].add(frame)

    def describe(self, full=False):
        s = "Receiver: \nfps = {}, slot = {:.2f}, start_time = {:.3f}\nQueues:".format(self.fps, 1/self.fps, self.startPlay)
        for q in self.queues:
            s += "\n" + q.describe(full)
        return s
