

def print_metrics(d):
    for streamer in d:
        print(streamer, ": ")
        for m in d[streamer]:
            print(" ", m, ": ", d[streamer][m])
