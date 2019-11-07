"""
File containing all
"""


from collections import deque
import numpy as np
import random


class Streamer(object):
    """Constains multiple Queue. One for each level of quality of a particular
    client.
    In particular, this object contains:

    streamer: The name of the streamer for indentification purpose
    qnames: Names of the queues that the streamer has.
    priority: queue priority. One streamer
              might have more importance than another streamer.
    arrival_rate: Expected arrival_rate of the source in KBps

    """

    Frame_Arrival = 0

    def __init__(self, streamer=0, qnames=0, priority=0, arrival_rate=0,
                 I_P_arrival_ratio=0, I_P_size_ratio=0, mean_frames=0,
                 var_frames=0, traces=0):
        self.deterministic = (streamer or qnames or priority or arrival_rate or
                              I_P_arrival_ratio or I_P_size_ratio or mean_frames
                              or var_frames)
        assert self.deterministic != bool(traces), "The system is either deterministic or random"
        assert(len(mean_frames) == len(var_frames) == len(qnames))
        assert(0 <= I_P_arrival_ratio <= 1)
        self.streamer = streamer
        self.priority = priority
        self.arrival_rate = arrival_rate  # In KBps for the highest quality lvl
        self.I_P_size_ratio = I_P_size_ratio
        self.I_P_arrival_ratio = I_P_arrival_ratio
        self.mean_frames = mean_frames  # ! Include also I frames
        self.var_frames = var_frames

        self.arrival_rates = [i * self.arrival_rate / max(self.mean_frames)
                              for i in mean_frames]

        # Create the queues
        self.queues = [Queue(qn) for qn in qnames]

    def describe(self, full=False):
        """Describe the current queue"""
        s = ("Streamer {}:\n priority = {}\n arrival rate = {}\n"
             "Queue(s): ").format(self.streamer, self.priority,
                                  self.arrival_rate)
        for q in self.queues:
            s += "\n"
            s += q.describe(full)
        return s

    def changeArrivalRate(self, rate):
        self.arrival_rate = rate
        self.arrival_rates = [i * self.arrival_rate / max(self.mean_frames)
                              for i in self.mean_frames]

    def update(self, arrival_stamp):
        """Generate incoming packet according to the arrival stamp

        Return the all the new updated frames of the last queue (last layer)
        """
        update_arrival_stamp = False

        new_arrival = []
        for stamp, timestamp in arrival_stamp:

            # An I frame or a P frame is coming
            IFrame = self.I_P_arrival_ratio > random.random()

            for q, mf, vf, br in zip(self.queues,
                                     self.mean_frames, self.var_frames, self.arrival_rates):

                # Size of the incoming frame
                mean = mf / (self.I_P_arrival_ratio * self.I_P_size_ratio + (1 - self.I_P_arrival_ratio))
                assert mean - 1.5 * vf > 0, "With these settings, it is likely to have negative frame size."

                if IFrame:
                    mean = mean * self.I_P_size_ratio

                s = round(np.random.normal(mean, vf), 2)

                f = Frame(s, Streamer.Frame_Arrival + stamp, IFrame,
                          origin=self.streamer, bitrate=br, timestamp=timestamp)
                q.add(f)

                if q == self.queues[-1]:
                    new_arrival.append(f)

        if update_arrival_stamp:
            Streamer.Frame_Arrival += len(arrival_stamp)

        return new_arrival

    def isEmpty(self):
        "Return true if all Queue are empty in the streamer."
        empty = True
        for q in self.queues:
            empty = empty and q.empty
        return empty

    def info(self):
        infos = []
        for q in self.queues:
            infos.append(q.info())

    def dequeue(self, queue_num, n=1):
        """Dequeue queues according to the queue number and
        the nuber of frame to be dequeued
        for instance, if queue_num=0 and n=3:
        3 frames of layer 0 (Base Layer) will be dequeued"""

        for i, q in enumerate(self.queues):
            if i == queue_num:
                frames = q.dequeue(n)
            else:
                q.dequeue(n)
        return frames


class Queue(object):

    def __init__(self, queue_name, default_load=[]):
        "arrival_rate: follow a lambda distribution of incomming packet"
        self.max_size = 500_000_000  # 500 MB Default value
        self.load = 0
        self.length = 0
        self.empty = True
        self.name = queue_name
        self.queue = deque()

        if len(default_load) != 0:
            load = 0
            for f in default_load:
                load += f.size
            if load > self.max_size:
                raise OverflowError("Initialization Overflow")
            self.load = load
            self.empty = False
            self.length = len(default_load)
            self.queue = deque(default_load)

    def dequeue(self, nb_frames):
        """Dequeue frames from the queue
        Return a list of Frames.
        """
        total_size = 0
        frames = []
        for i in range(nb_frames):
            f = self.queue.popleft()
            total_size += f.size
            frames.append(f)

        self.load -= total_size
        self.length -= nb_frames
        self.empty = True if 0 == self.length else False

        return frames

    def flush(self):
        "Flush the queue"
        del self.queue
        self.queue = deque()

    def describe(self, full=False):
        "Return a string description of the queue"
        s = "{} : ".format(self.name)
        if full:
            s += '\n'
        if self.empty:
            return s + "Empty  "
        for f in self.queue:
            s += f.describe(full)
        return s[:-2]

    def getFrames(self, n):
        "Get the n first frames or m < n if the queue only contains m frames"
        frames = []
        i = 0
        for f in self.queue:
            frames.append(f)
            i += 1
            if i == n:
                break
        return frames

    def add(self, frame):
        if self.load + frame.size < self.max_size:
            self.queue.append(frame)
            self.length += 1
            self.load += frame.size
            self.empty = False
        else:
            raise OverflowError("Queue is full")


class Frame:
    """A Frame object.
    It is defined by:
     its size in KB, `size`
     its arrival order, `order`
     its type. Either Iframe (Iframe=True) or Pframe (Iframe=false)
         regarding the tyoe of the frame
     its origine `origine`  """

    def __init__(self, size, order, Iframe, origin="unkown", bitrate=None, timestamp=None, availability=None):
        self.size = size
        self.order = order
        self.Iframe = Iframe
        self.origin = origin
        self.bitrate = bitrate
        self.timestamp = timestamp
        self.sent = None
        self.last_sent = None
        self.availability = availability

    def describe(self, full=False):
        fs = "Iframe" if self.Iframe else "Pframe"
        s = "{} #{}: {}Kb | ".format(fs, self.order, self.size)
        if full:
            available = -1 if self.availability is None else self.availability % 100
            available = -1 if self.availability is None else self.availability % 100
            available = -1 if self.availability is None else self.availability % 100

            s = ("   {} #{}: {}Kb from {}, stamp={:.4f} "
                 "avail={:.4f}, br={:.1f} \n").format(fs, self.order, self.size,
                                                 self.origin, self.timestamp % 100,
                                                 available, self.bitrate)

        return s
