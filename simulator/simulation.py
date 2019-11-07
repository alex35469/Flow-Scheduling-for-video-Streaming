#! python3
"""Simulate the system
"""

from scheduler import RandomScheduler, FIFOScheduler
from stream import Streamer, Queue
from time import time
from channel import StableChannelNoWindow, NetworkTracesChannel
from receiver import Receiver
from utils import print_metrics, read_network_trace


# ############ ENVIRONEMENT ####################

# ----- Streamer ------
alice = Streamer(streamer="Alice", qnames=["Base", "Enhanced"], priority=2,
                 arrival_rate=150, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                 mean_frames=[8, 10], var_frames=[0, 0])

bob = Streamer(streamer="Bob", qnames=["Base", "Enhanced"], priority=2,
               arrival_rate=100, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
               mean_frames=[5, 6], var_frames=[0, 0])

carlos = Streamer(streamer="Carlos", qnames=["Base", "Enhanced"], priority=2,
                  arrival_rate=2000, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                  mean_frames=[5, 6], var_frames=[0, 0])

dave = Streamer(streamer="Dave", qnames=["Base", "Enhanced"], priority=2,
                arrival_rate=500, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                mean_frames=[5, 6], var_frames=[0, 0])

streamers = [alice, bob]

# ----- Scheduler ------
# rs = RandomScheduler(streames=streamers)
rs = FIFOScheduler(streames=streamers)


# ----- Channel ------
# sc = StableChannelNoWindow(bandwidth=1000)

# network traces
path_huabei = "/traces/huabei/liveldResult_2019-05-12.txt"
sc = NetworkTracesChannel(path_huabei, 0.5)

# ----- Receiver ------
receiver_buffer_size = -1  # Not yet known
receiver = Receiver(queues=[Queue(s.streamer) for s in streamers], fps=30)


# ############ SIMULATION ####################

N = 100
total_received = 0
receiver.start(waiting=0)

# Follow network traces
cumultime = 0
tstart = time()
while cumultime < 3:


    frames = rs.decide(dprint=False)

    if frames:
        total_received += len(frames)
        sc.send_frames(frames, time() - tstart)
        receiver.receive(frames)

    tstop = time()
    rs.update(tstart, tstop)
    tstart = time()
    # change the bandwidth
    cumultime += tstop - tstart

print(receiver.describe(full=True))
metrics = receiver.playback()
print_metrics(metrics)
