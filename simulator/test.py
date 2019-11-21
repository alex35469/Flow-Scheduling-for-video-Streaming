#! python3
import unittest
from stream import Frame, Queue, Streamer
from scheduler import RandomScheduler
from time import time
from receiver import Receiver
from utils import get_scaled_time

class FrameTestCase(unittest.TestCase):

    def test_frame_attribute(self):
        f = Frame(91, 3, True)
        self.assertEqual(f.size, 91, "Should be 91")
        self.assertEqual(f.order, 3)
        self.assertTrue(f.Iframe)


class QueueTestCase(unittest.TestCase):
    def setUp(self):
        self.q_base1 = Queue(queue_name="Base")
        self.q_base1.add(Frame(23, 1, True))

        self.q_base2 = Queue(queue_name="Enhance", default_load=[Frame(91, 3, True), Frame(20, 4, False)])
        self.q_base2.add(Frame(12, 5, False))

    def test_add_and_load(self):
        self.q_base1.add(Frame(22, 2, False))
        self.q_base1.add(Frame(10, 3, False))
        self.assertEqual(self.q_base1.load, 55)
        self.assertEqual(self.q_base2.load, 123)

    def test_length(self):
        self.assertEqual(self.q_base1.length, 1)
        self.assertEqual(self.q_base2.length, 3)

    def test_getFrames(self):
        self.assertEqual(len(self.q_base2.getFrames(100)), 3)
        self.assertEqual(len(self.q_base2.getFrames(2)), 2)
        self.assertEqual(self.q_base1.getFrames(1)[0].size, 23)

    def test_dequeue(self):
        # Test q1
        l1 = self.q_base1.dequeue(1)
        self.assertTrue(self.q_base1.empty)
        self.assertEqual(self.q_base1.load, 0)
        with self.assertRaises(IndexError):
            self.q_base1.dequeue(1)

        self.assertEqual(l1[0].size, 23)

        l2 = self.q_base2.dequeue(2)
        self.assertEqual(l2[1].size, 20)
        self.assertEqual(self.q_base2.load, 12)

    def test_overflow(self):
        self.q_base1


class StreamerTestCase(unittest.TestCase):
    def setUp(self):
        pass
        #s1 = Streamer(streamer="Bob", qnames=["Base", "Enhance"], 2, 5,
        #           I_P_arrival_ratio=0.2, quality_ratio=0.3,
        #           mean_frames=[3,4], var_frames=[1,1])


class SchedulerTestCase(unittest.TestCase):
    def setUp(self):
        # Create two streamers
        self.alice = Streamer(streamer="Alice", qnames=["Base", "Enhanced"], priority=2,
                         arrival_rate=20, I_P_arrival_ratio=0.8, I_P_size_ratio=2,
                         mean_frames=[30, 50], var_frames=[0, 0])

        self.bob = Streamer(streamer="Bob", qnames=["Base", "Enhanced"], priority=2,
                            arrival_rate=60, I_P_arrival_ratio=0.5, I_P_size_ratio=10,
                            mean_frames=[30, 40], var_frames=[0, 0])

        # The scheduler to use
        self.rs = RandomScheduler(streames=[self.alice, self.bob])

    #@unittest.skip("take approx. 10 sec to run")
    def test_empiricalArrivalRate(self):
        SPEED_FORWARD = 1000
        get_time = get_scaled_time(scale=SPEED_FORWARD)
        ttime = 0
        tkb = 0
        tstart = get_time()
        loop = 0
        while ttime < 4800:  # 2400 sec = 30 min
            tstop = get_time()

            updated_frames = self.rs.update(tstart, tstop)
            ttime += tstop - tstart

            tstart = get_time()

            self.rs.decide()
            total_kb = sum([f.size for f in updated_frames])
            tkb += total_kb
            tstop = get_time()
            loop += 1

        print("average_intertime = ", ttime/loop)
        expected_total = sum([s.arrival_rate for s in self.rs.streamers])
        delta = expected_total/100  # 1% of the total arrival rate

        self.assertAlmostEqual(tkb/ttime, self.alice.arrival_rate + self.bob.arrival_rate, delta=delta)


class ReceiverTestCase(unittest.TestCase):
    def setUp(self):
        streamers = ["alice", "bob", "carlos", "davis", "egbert"]
        self.oqdict = {"alice":0, "bob":1, "carlos":2, "davis":3, "egbert":4}
        self.receiverFull = Receiver(queues=[Queue(s) for s in streamers], fps=30)
        self.receiverSimple = Receiver(queues=[Queue(s) for s in streamers[:2]], fps=30)

    def test_attributes(self):
        self.assertEqual(self.receiverFull.originQueueDict,  self.oqdict)

    def test_receive(self):
        # Create frames
        af1, af3 = Frame(91, 1, True, "alice"), Frame(91, 3, True, "alice")
        bf2 = Frame(30, 2, False, "bob")
        self.receiverFull.receive([af1, bf2, af3])

        self.assertEqual(self.receiverFull.queues[self.oqdict["alice"]].dequeue(1)[0], af1)
        self.assertEqual(self.receiverFull.queues[self.oqdict["alice"]].dequeue(1)[0], af3)
        self.assertEqual(self.receiverFull.queues[self.oqdict["bob"]].dequeue(1)[0], bf2)

    def test_playback(self):
        self.receiverSimple.lastPlay = [15]*len(self.receiverSimple.queues)

        # TEST One frame each received
        af1 = Frame(10, 1, False, "alice", bitrate=500, timestamp=15.002, availability=15.005)
        bf2 = Frame(60, 2, True, "bob", bitrate=600, timestamp=15.5, availability=16.5)
        self.receiverSimple.receive([af1, bf2])
        results = self.receiverSimple.playback()
        expected = {"alice" : {"total_rebuffering_event" :1,
                            "total_rebuffering_time" : 0.005,
                            'total_delay': 0.003,
                            "average_rate": 500.0,
                            "total_frame": 1}
                            ,
                    "bob" : {"total_rebuffering_event" :1,
                             "total_rebuffering_time" : 1.5,
                             'total_delay': 1.0,
                             "average_rate": 600.0,
                             "total_frame": 1}}
        self.assertEqual(results, expected)

        # TEST 2 frames received only one streamer
        bf3 = Frame(60, 4, True, "bob", bitrate=700, timestamp=15.7, availability=15.8)
        bf4 = Frame(60, 5, True, "bob", bitrate=300, timestamp=15.7, availability=15.8)
        self.receiverSimple.receive([bf3, bf4])
        results = self.receiverSimple.playback()

        expected = {"alice" : 0,
                    "bob" : {"total_rebuffering_event" :0,
                             "total_rebuffering_time" : 0,
                             'total_delay': round(16.533 - 15.7 + 16.566 -15.7, 2),
                             "average_rate": 500.0,
                             "total_frame": 2}}
        self.assertEqual(results, expected)
        # Check playing time for alice and bob
        self.assertAlmostEqual(self.receiverSimple.lastPlay[0],
                               af1.availability + 1/self.receiverSimple.fps)
        self.assertAlmostEqual(self.receiverSimple.lastPlay[1],
                               bf2.availability + 3 * 1/self.receiverSimple.fps)


        # TEST 2 frames received each (Alice has high latency, Bob high rebuffering)
        bf5 = Frame(90, 4, True, "bob", bitrate=250, timestamp=16.05, availability=16.06)
        af6 = Frame(60, 5, False, "alice", bitrate=300, timestamp=13.0, availability=14.6)
        bf7 = Frame(60, 4, True, "bob", bitrate=350, timestamp=19.04, availability=19.05)
        af8 = Frame(60, 4, True, "alice", bitrate=400, timestamp=14.0, availability=14.06)

        self.receiverSimple.receive([bf5, af6, bf7, af8])
        results = self.receiverSimple.playback()
        expected = {"alice" : {"total_rebuffering_event" :0,
                            "total_rebuffering_time" : 0.0,
                            'total_delay': round(15.038333333333334 -13  + 15.038333333333334 + 0.0333333333 - 14.0, 2),
                            "average_rate": 350.0,
                            "total_frame": 2},
                    "bob" : {"total_rebuffering_event" :1,
                             "total_rebuffering_time" : 2.416667,
                             'total_delay': 0.54 + 0.01 + 0.01,
                             "average_rate": 300.0,
                             "total_frame": 2}}

        self.assertEqual(results, expected)
if __name__ == '__main__':
    unittest.main()
