"""
Emulation of the receiver that will consume de stream.
Contains:
"""
from time import time


class Receiver:
    """Represents the receiver. """

    MAX_BUFFER = 1_000_000  # Buffer size in KB

    def __init__(self, queues, fps):
        self.queues = queues
        self.fps = fps
        self.lastPlay = [0] * len(queues)  # time of the begining of the last frame played
        self.originQueueDict = dict([(q.name, i) for i, q in enumerate(queues)])
        self.isPlaying = [False] * len(queues)
        self.started = False
        self.startPlay = -1

    def playback(self, info=False, N=0):
        """Play the frames in the queues independently overtime.
        i.e. at the end of the simulation

        if info=True, only gives the QoE but does not play the frames.

        pros: no time consumption during simulation
        cons: Rewards only come at the end (of the playing)

        Return:
        dictionary-like results

        {queue 1 :  total_rebuffering_event
                    total_rebuffering_time
                    total_delay
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
            i = 0

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
                total_delay += lastPlay - f.timestamp
                average_rate += f.bitrate
                total_frame += 1
                # fast forward to the end of the playing frame
                lastPlay += frame_slot

                i += 1
                if i == N and bool(N):
                    break

            if total_frame == 0:
                results[q.name] = 0
                continue

            results[q.name] = {"total_rebuffering_event": total_rebuffering_event,
                               "total_rebuffering_time": round(total_rebuffering_time, 6),
                               "total_delay": round(total_delay, 6),
                               "average_rate": average_rate / total_frame,
                               "total_frame": total_frame}

            # We do not update the receiver server state
            if info:
                continue

            # update the player state
            self.lastPlay[self.originQueueDict[q.name]] = lastPlay

            if bool(N):
                q.dequeue(i)
            else:
                q.flush()

        return results

    def start(self, waiting=0):
        """Inititate the playing process"""
        self.lastPlay = [time() + waiting] * len(self.queues)
        self.startPlay = self.lastPlay[-1]

    def receive(self, frames):
        for frame in frames:
            queue_nb = self.originQueueDict.get(frame.origin)
            if type(queue_nb) is int:
                self.queues[queue_nb].add(frame)

    def describe(self, full=False):
        s = "Receiver: \nfps = {}, slot = {:.3f}, start_time = {:.3f}\nQueues:".format(self.fps, 1 / self.fps, self.startPlay)
        for q in self.queues:
            s += "\n" + q.describe(full)
        return s
