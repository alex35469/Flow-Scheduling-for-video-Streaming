#! python3
"""Simulate the system
"""

from scheduler import RandomScheduler, FIFOScheduler
from stream import Streamer, Queue
from time import time
from channel import StableChannelNoWindow
from receiver import Receiver
from utils import print_metrics


# ############ ENVIRONEMENT ####################
# Create two streamers
alice = Streamer(streamer="Alice", qnames=["Base", "Enhanced"], priority=2,
                 arrival_rate=1500, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                 mean_frames=[8, 10], var_frames=[0, 0])

bob = Streamer(streamer="Bob", qnames=["Base", "Enhanced"], priority=2,
               arrival_rate=1000, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
               mean_frames=[5, 6], var_frames=[0, 0])

carlos = Streamer(streamer="Carlos", qnames=["Base", "Enhanced"], priority=2,
                  arrival_rate=2000, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                  mean_frames=[5, 6], var_frames=[0, 0])

dave = Streamer(streamer="Dave", qnames=["Base", "Enhanced"], priority=2,
                arrival_rate=500, I_P_arrival_ratio=0.2, I_P_size_ratio=5,
                mean_frames=[5, 6], var_frames=[0, 0])

streamers = [alice, bob]

# The scheduler to use
rs = RandomScheduler(streames=streamers)
rs = FIFOScheduler(streames=streamers)
# The channel model
sc = StableChannelNoWindow(1000)


# receiver
receiver_buffer_size = -1  # Not yet known
receiver = Receiver(queues=[Queue(s.streamer) for s in streamers], fps=30)


# ############ SIMULATION ####################


N = 100
total_received = 0
receiver.start(waiting=0)
while total_received < N:
    # Scheduler
    tstart = time()
    frames = rs.decide(dprint=False)

    if frames:
        total_received += len(frames)
        sc.send_frames(frames)
        receiver.receive(frames)
    tstop = time()

    rs.update(tstart, tstop)


metrics = receiver.playback(N=2, info=True)
print_metrics(metrics)

metrics = receiver.playback(N=2, info=False)
print_metrics(metrics)

print("----")

print(receiver.describe())
metrics = receiver.playback(N=2, info=True)
print(metrics)
print_metrics(metrics)

metrics = receiver.playback(N=2, info=True)
print_metrics(metrics)
