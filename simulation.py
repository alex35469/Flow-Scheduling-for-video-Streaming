#! python3
"""Simulate the system
"""

from scheduler import RandomScheduler
from stream import Streamer, Queue
from time import time
from channel import StableChannelNoWindow
from receiver import Receiver

N = 15  # Batch size
Bandwith = 3  # Mbps
# ############ ENVIRONEMENT ####################! python3
# Create two streamers
alice = Streamer(streamer="Alice", qnames=["Base", "Enhanced"], priority=2,
                 arrival_rate=6000, I_P_arrival_ratio=0, I_P_size_ratio=10,
                 mean_frames=[5, 6], var_frames=[0, 0])

bob = Streamer(streamer="Bob", qnames=["Base", "Enhanced"], priority=2,
               arrival_rate=6000, I_P_arrival_ratio=0, I_P_size_ratio=10,
               mean_frames=[5, 6], var_frames=[0, 0])

streamers = [alice, bob]
# The scheduler to use
rs = RandomScheduler(streames=streamers)


# The channel model
sc = StableChannelNoWindow(150000)


# receiver
receiver_buffer_size = -1  # Not yet known
receiver = Receiver(queues=[Queue(s.streamer) for s in streamers], fps=30)


total_received = 0
receiver.start()
while total_received < 100:
    # Scheduler
    tstart = time()
    frames = rs.decide()

    if frames:
        total_received += len(frames)
        sc.send_frames(frames)
        # receiver
        receiver.receive(frames)

    tstop = time()
    rs.update(tstart, tstop)

print(receiver.describe(True))
metrics = receiver.playback()
print(metrics)
