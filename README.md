# Flow Scheduling for Video Streaming
Author: Alexandre Dumur & XiaoYu

For a gloabl view point, please refer to the slides: Project overview.odp

## Overview

### Description
In multiparty live streaming, each client upload their video to a central server by encoding it with Scalable Video Coding (SVC) at different quality. The server is then in charge of redistributing every streaming content to each client. In order to keep the Quality of Experience (QoE) as high as possible, clever scheduling has to be made, i.e., which stream to distribute to a client first and at which quality. Multiple parameters have to be taken into account: 

1. There are different priorities for different flows.
2. A flow contains different quality of video streams.
3. A flow has to be delivered in time to the client to not exceed a delay constraint
4. The streaming content contains I-frame and P-frame that can be handled differently by the scheduler.

### Goal
The goal of the project is to design a flow scheduling algorythm applied to live multicast video streaming. Create a simulator and evaluate the system. 


## Structure

The Repository consists of 5 main files:

1. simulation.py:
  Simulate the system (c.f. next section).
2. stream.py:
  Define ´Frame´, `Queue` and `Streamer` objects.
3. scheduler:
  Backbone of the project. Define the Abstract class `Scheduler` which will assess the perfomence of the system. (c.f. Scheduler in the next section)
4. receive.py: 
  Emulate the receiver and `playback()` function that output the metrics used to compute the Quality of Experience (QoE).
5. channel.py:
  Emulate the channel through the function `send_frames(frames)` by changeing the availability attributes contained in the object Frame 
  
## Simulation

### Input & Output
The simulation takes different variable as input (the environement) and output at the end of 
the script or at each step of the main loop the metrics that can be used to compute the QoE. (i.e.: latency, rebuffering time...)

The inputs (inside ENVIRONEMENT section) are defined by:
  - Streamers: all streamers defined by the arrival rate of their streames
  
### Model
- Sequential implementation written in python (321 LOC so far, excluding tests)
- Sources are modeled as poisson process to generate the number of new frame arrival for each source. Frame size is modeled as a Gaussian Process
- Time for the scheduler to decide which frame to send is recorded and queues a reupdated accordingly
- The simulator can decide: 
  1. the frame from which streamer to send first. 
  2. At which quality should the frame be sent. 
  3. Drop a frame to reduce latency (only for P-frame)
- Flexible implementation, consisting of 5 modules (stream.py, scheduler.py, channel.py,
simulation.py, receiver.py) where each module can be re-implemented, improve without disturbing other model.
- Simulator does not need to play the actual video. (Speedup gain: ~36000x)
- Can generate as many data as we want 

### Scheduler
The QoE depends strongly of the choice of the scheduler. A scheduler can be implemented as a class that herits from the abstract class Scheduler.

It must implement only one function: ´decide()´ which decides the frames to send from 

So far, 2 scheduler have been implemented: 
- `RandomScheduler`: Bad Scheduler. Make Decision randomley
- `FIFOScheduler`: Decide on a first-in-first-out basis. (number of frame to be decided is picked at random)


### Future Work 
- Provide a better model of the channel (For now, only compute the transmission delay as a product of the frame size and the bandwith)
- Integrate real network traces and frame arrival to compare the real world to the simulator
- Design a scheduler that can beat the simple FIFO scheduler based on a predefined QoE function. 

