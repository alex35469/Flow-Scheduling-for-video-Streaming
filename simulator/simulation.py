#! python3
"""Simulate the system
"""

from scheduler import RandomScheduler, FIFOScheduler
from stream import Streamer, Queue
from time import time
from channel import StableChannelNoWindow, NetworkTracesChannel
from receiver import Receiver
from utils import print_metrics, read_network_trace, get_scaled_time


### SIMULATION VARIABLE
SPEED_FORWARD = 400  # gain compare to the real speed time
MAX_INTERTIME_UPDATE_DURATION = 0.1  # maximum time spent between 2 updates

# ############ ENVIRONEMENT ####################

# ----- Streamer ------
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

# ----- Scheduler ------
# rs = RandomScheduler(streames=streamers)
rs = FIFOScheduler(streames=streamers)


# ----- Channel ------
# sc = StableChannelNoWindow(bandwidth=1000, scale_time=SPEED_FORWARD)

# network traces
path_huabei = "/traces/huabei/liveldResult_2019-05-12.txt"
sc = NetworkTracesChannel(path_huabei, 0.5, scale_time=SPEED_FORWARD)

# ----- Receiver ------
receiver_buffer_size = -1  # Not yet known
receiver = Receiver(queues=[Queue(s.streamer) for s in streamers],
                    fps=30, scaled_time=SPEED_FORWARD)


# ############ SIMULATION ####################

get_time = get_scaled_time(scale=SPEED_FORWARD)
N = 100
total_received = 0
receiver.start(waiting=0)

# Follow network traces
cumultime = 0
loop = 0
while cumultime < 4800:  # 1 hour simulation

    tstart = get_time()

    frames = rs.decide(dprint=False)

    if frames:
        total_received += len(frames)
        sending_time = get_time() - tstart
        sc.send_frames(frames, sending_time)
        receiver.receive(frames)

    tstop = get_time()
    rs.update(tstart, tstop)
    elapsed = tstop - tstart
    if elapsed > MAX_INTERTIME_UPDATE_DURATION:  # 2920.00
        print("Warning: Elapsed time between 2 updates is too large\nelased={} Max={}".format(elapsed, MAX_INTERTIME_UPDATE_DURATION))
    cumultime += elapsed
    loop += 1
print("Cumul = ", cumultime)
# print(receiver.describe(full=True))
metrics = receiver.playback()
print_metrics(metrics)
