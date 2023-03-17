from time import time, sleep
import mido
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index
from audio import Audio
from video import Video

MIDDLE_C = 60

class Listener:
    def __init__(self, df):
        self.df = df
        # Setup audio
        # self.outport = mido.open_output('IAC Driver creatures')
        self.inport = mido.open_input()

    def run(self, i):

        ticks = 0

        print('Ready for midi...')

        for msg in self.inport:
            if msg.type == 'clock':
                if ticks % 6 == 0:
                    print('quarter beat')
                    i.value = i.value + 1
                    # print(i.value)
                ticks = ticks + 1


def listener(i, df):
    my_listener = Listener(df)
    my_listener.run(i)

def devices_loop(i, df):
    my_devices = Devices(df)
    my_devices.run(i)

def audio_loop(i, df):
    my_audio = Audio(df)
    my_audio.run(i)

def video_loop(i, df):
    my_video = Video(df)
    my_video.run(i)
        
if __name__ == "__main__":
    
    mp.set_start_method('forkserver')

    df = load_data(cached=True)

    i = mp.Value('i', get_start_index(df))
    
    p1 = mp.Process(target=listener, args=(i, df))
    p2 = mp.Process(target=devices_loop, args=(i, df))
    p3 = mp.Process(target=audio_loop, args=(i, df))
    p4 = mp.Process(target=video_loop, args=(i, df))

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()
