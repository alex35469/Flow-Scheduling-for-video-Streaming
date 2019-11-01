import io
import sys


def read_network_trace(path):
    "Return a generator that outputs the trace"
    def read_nt():
        with open(path) as nt:
            for line in nt:
                line = line.strip()
                if str.isdigit(line):
                    yield line
    return read_nt


def read_frame_trace(path):
    "Return a generator that outputs the trace"
    def read_nt():
        with open(path) as nt:
            for line in nt:
                line = line.strip()
                if str.isdigit(line):
                    yield line
    return read_nt

def print_metrics(d):
    for streamer in d:
        print(streamer, ": ")
        for m in d[streamer]:
            print(" ", m, ": ", d[streamer][m])
