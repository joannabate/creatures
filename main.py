from time import time
import mido
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index
from audio import Audio
from video import Video
from sensor import Sensor

class Listener:
    def __init__(self):
        self.inport = mido.open_input()

    def run(self, i, bpm):

        ticks = 0

        print('Ready for midi...')

        i_time_last = time()

        for msg in self.inport:
            if msg.type == 'clock':
                    if ticks % 6 == 0:
                        i.value = i.value + 1

                        i_time = time()
                        bpm.value = int(4*4/(i_time - i_time_last))
                        i_time_last = i_time

                    ticks = ticks + 1

def listener(i, bpm):
    my_listener = Listener()
    my_listener.run(i, bpm)

def devices_loop(i, df):
    my_devices = Devices(df)
    my_devices.run(i)

def audio_loop(i, step_on_flag, df):
    my_audio = Audio(df)
    my_audio.run(i, step_on_flag)

def video_loop(i, bpm, step_on_flag, df):
    my_video = Video(df)
    my_video.run(i, bpm, step_on_flag)

def sensor_loop(step_on_flag):
    my_sensor = Sensor()
    my_sensor.run(step_on_flag)

if __name__ == "__main__":
    
    mp.set_start_method('forkserver')

    df = load_data(cached=True)

    i = mp.Value('i', get_start_index(df))
    bpm = mp.Value('i', 0)
    step_on_flag = mp.Value('b', False)
    
    p1 = mp.Process(target=listener, args=(i, bpm))
    p2 = mp.Process(target=devices_loop, args=(i, df))
    p3 = mp.Process(target=audio_loop, args=(i, step_on_flag, df))
    p4 = mp.Process(target=video_loop, args=(i, bpm, step_on_flag, df))
    p5 = mp.Process(target=sensor_loop, args=(step_on_flag,))

    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()
