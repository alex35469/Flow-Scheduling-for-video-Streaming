#! python3
"""
Modeling of the Channel.
This include a the sending delay, and transmission delay
"""
from abc import ABC, abstractmethod
from utils import read_network_trace, get_scaled_time


class Channel(ABC):
    def __init__(self, scale_time=1):
        self.get_time = get_scaled_time(scale_time)

    @abstractmethod
    def send_frames(self, frames):
        """Sends data to the channel.
        update availability field of Frames
        """


class StableChannelNoWindow(Channel):
    "Very Simple channel modulation where tansport layer is not modeled"
    def __init__(self, bandwidth, sending_delay=0, scale_time=1):
        super().__init__(scale_time)
        self.bandwidth = bandwidth
        self.sending_delay = sending_delay

    def send_frames(self, frames):
        """update availability field of Frames
        Return list of time that
        """
        for f in frames:
            f.availability = self.get_time() + f.size / self.bandwidth + self.sending_delay

    def changeBandwith(self, bandwidth):
        self.bandwidth = bandwidth


class NetworkTracesChannel(Channel):
    "Very Simple channel modulation where tansport layer is not modeled"
    def __init__(self, path, traces_intertime, scale_time=1):
        super().__init__(scale_time)
        self.trace_generator = read_network_trace(path)()
        self.traces_intertime = traces_intertime
        self.current_time = 0
        self.current_bandwidth = next(self.trace_generator)
        self.queue = []

    def get_next_bandwidth(self, elapsed):
        t_left = self.traces_intertime - self.current_time % self.traces_intertime
        self.current_time += elapsed
        print("Cumulated current time: ", self.current_time)
        if elapsed < t_left:
            return self.current_bandwidth

        to_fwd = int((elapsed - t_left) // self.traces_intertime) + 1
        for _ in range(to_fwd):
            bandwidth = next(self.trace_generator)
        self.current_bandwidth = bandwidth
        return self.current_bandwidth


    def update_availability_frame_sent(self, old_bandwidth):

        new_queue = []

        print("Bandwidth is being updated: {} old -> {}".format(old_bandwidth,
                                                                self.current_bandwidth))
        if self.current_bandwidth == 0:
            for f, _ in self.queue:
                t = self.get_time()
                if frame.availability >= t:
                    frame.availability = None
                    updated_kb_sent = elapsed * old_bandwidth + kb_sent



        for frame, kb_sent in self.queue:
            t = self.get_time()

            # The frame is already available in
            if frame.availability is not None and frame.availability < t:
                continue

            updated_kb_sent = kb_sent
            # compute the new availability here
            if self.current_bandwidth == 0:
                # Introduce some bias since it does not consider the kb that has been sent before switching to 0
                frame.availability = None

            elif frame.availability is None:
                frame.availability = t + (frame.size - kb_sent) / self.current_bandwidth
                frame.sent = t

            else:
                elapsed = t - frame.sent
                frame.availability = t + max((frame.size - kb_sent)/ self.current_bandwidth, 0)
                updated_kb_sent = elapsed * old_bandwidth + kb_sent

            new_queue.append((frame, updated_kb_sent))

        self.queue = new_queue

    def send_frames(self, frames, elapsed):
        """update availability field of Frames
        Return list of time that
        """
        old_bandwidth = self.current_bandwidth
        self.current_bandwidth = self.get_next_bandwidth(elapsed)
        if old_bandwidth != self.current_bandwidth:
            self.update_availability_frame_sent(old_bandwidth)

        for f in frames:
            if self.current_bandwidth > 0:
                f.sent = self.get_time()
                print(f.describe(), " => sent at ", f.sent)
                f.availability = f.sent + f.size / self.current_bandwidth

            self.queue.append((f, 0))


# Simple test
if __name__ == "__main__":
    from random import random

    # network traces
    path_huabei = "/traces/huabei/liveldResult_2019-05-12.txt"
    first_20_traces = [0, 1872, 1312, 1344, 832, 416, 424, 1840, 888, 1352,
                       1352, 1424, 1408, 1416, 1424, 1352, 1152, 768]
    time_trace_zip = [(trace, i * 0.5) for i, trace in enumerate(first_20_traces)]

    sc = NetworkTracesChannel(path_huabei, 0.5)
    cum_elapsed = 0
    for _ in range(20):
        elapsed = random() / 2
        cum_elapsed += elapsed
        to_pick = int(cum_elapsed //0.5)
        #  get_next_bandwidth error
        assert sc.get_next_bandwidth(elapsed), first_20_traces[to_pick]

# Maybe to simulate the window consider the length of frames
