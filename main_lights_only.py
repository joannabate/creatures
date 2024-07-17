from time import sleep
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index

BPM = 100

class Clock:
    def __init__(self):
        return
    
    def run(self, i):
        while True:
            # Loop round at end of day
            i.value = (i.value + 1) % 525600

            # print(i.value)

            sleep(BPM/(60*4*4))


def clock_loop(i):
    my_clock = Clock()
    my_clock.run(i)

def devices_loop(i, df, sensor_flags):
    my_devices = Devices(df)
    my_devices.run(i, sensor_flags)

if __name__ == "__main__":
    
    mp.set_start_method('forkserver')

    df = load_data(cached=True)

    i = mp.Value('i', get_start_index(df))

    sensor_flags = None
    
    p1 = mp.Process(target=clock_loop, args=(i,))
    p2 = mp.Process(target=devices_loop, args=(i, df, sensor_flags))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

