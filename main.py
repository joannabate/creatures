from time import time, sleep
import mido
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index
from audio import Audio
from video import Video

MIDDLE_C = 60

class Listener:
    def __init__(self):
        self.inport = mido.open_input()

    def run(self, i):

        ticks = 0

        print('Ready for midi...')

        for msg in self.inport:
            if msg.type == 'clock':
                if ticks % 6 == 0:
                    i.value = i.value + 1
                ticks = ticks + 1


def listener(i):
    my_listener = Listener()
    my_listener.run(i)

def devices_loop(i, df):
    my_devices = Devices(df)
    my_devices.run(i)

def audio_loop(i, df, element):
    my_audio = Audio(df)
    my_audio.run(i, element)

def video_loop(i, df, element):
    my_video = Video(df)
    my_video.run(i, element)


if __name__ == "__main__":
    
    mp.set_start_method('forkserver')

    df = load_data(cached=True)

    i = mp.Value('i', get_start_index(df))
    element = mp.Value('i', 0)
    
    p1 = mp.Process(target=listener, args=(i,))
    p2 = mp.Process(target=devices_loop, args=(i, df))
    p3 = mp.Process(target=audio_loop, args=(i, df, element))
    p4 = mp.Process(target=video_loop, args=(i, df, element))

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()
