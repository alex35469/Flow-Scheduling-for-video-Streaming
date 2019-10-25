#! python3
import unittest
from stream import Frame, Queue, Streamer
from scheduler import RandomScheduler
from time import time
from receiver import Receiver

class FrameTestCase(unittest.TestCase):

    def test_frame_attribute(self):
        f = Frame(91, 3, True)
        self.assertEqual(f.size, 91, "Should be 91")
        self.assertEqual(f.order, 3)
        self.assertTrue(f.Iframe)

    def test_frame_timestamp(self):
        f = Frame(43, 2, True)
        t1 = time()
        self.assertAlmostEqual(t1, f.timestamp, delta=0.01)


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
                            mean_frames=[30, 40], var_frames=[0, 7])

        # The scheduler to use
        self.rs = RandomScheduler(streames=[self.alice, self.bob])

    @unittest.skip("take approx. 10 sec to run")
    def test_empiricalArrivalRate(self):

        ttime = 0
        tkb = 0
        for N in range(1_000_000):
            elapsed = 0.1
            updated_frames = self.rs.update(elapsed=elapsed)
            self.rs.decide()
            # print(rs.describe())
            total_kb = sum([f.size for f in updated_frames])
            tkb += total_kb
            ttime += elapsed

        expected_total = sum([s.arrival_rate for s in self.rs.streamers])
        delta = expected_total/100  # 1% of the total arrival rate

        self.assertAlmostEqual(tkb/ttime, self.alice.arrival_rate + self.bob.arrival_rate, delta=delta)


class ReceiverTestCase(unittest.TestCase):
    def setUp(self):
        streamers = ["alice", "bob", "carlos", "davis", "egbert"]
        self.oqdict = {"alice":0, "bob":1, "carlos":2, "davis":3, "egbert":4}
        self.receiver = Receiver(queues=[Queue(s) for s in streamers], fps=30)

    def test_attributes(self):
        self.assertEqual(self.receiver.originQueueDict,  self.oqdict)

    def test_receive(self):
        # Create frames
        af1, af3 = Frame(91, 1, True, "alice"), Frame(91, 3, True, "alice")
        bf2 = Frame(30, 2, False, "bob")
        self.receiver.receive([af1, bf2, af3])

        self.assertEqual(self.receiver.queues[self.oqdict["alice"]].dequeue(1)[0], af1)
        self.assertEqual(self.receiver.queues[self.oqdict["alice"]].dequeue(1)[0], af3)
        self.assertEqual(self.receiver.queues[self.oqdict["bob"]].dequeue(1)[0], bf2)

if __name__ == '__main__':
    unittest.main()
