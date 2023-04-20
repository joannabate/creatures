from time import time
import mido
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index
from audio import Audio
from video import Video
from sensors import Sensors

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

def devices_loop(i, df, sensor_flags):
    my_devices = Devices(df)
    my_devices.run(i, sensor_flags)

def audio_loop(i, df, sensor_flags):
    my_audio = Audio(df)
    my_audio.run(i, sensor_flags)

def video_loop(i, bpm, df):
    my_video = Video(df)
    my_video.run(i, bpm)

def sensors_loop(sensor_flags):
    my_sensors = Sensors()
    my_sensors.run(sensor_flags)

if __name__ == "__main__":
    
    mp.set_start_method('forkserver')

    df = load_data(cached=True)

    i = mp.Value('i', get_start_index(df))
    bpm = mp.Value('i', 0)
    s1 = mp.Value('b', False)
    s2 = mp.Value('b', False)
    s3 = mp.Value('b', False)
    s4 = mp.Value('b', False)

    sensor_flags = [s1, s2, s3, s4]
    # sensor_flags = None
    
    p1 = mp.Process(target=listener, args=(i, bpm))
    p2 = mp.Process(target=devices_loop, args=(i, df, sensor_flags))
    p3 = mp.Process(target=audio_loop, args=(i, df, sensor_flags))
    p4 = mp.Process(target=video_loop, args=(i, bpm, df))
    p5 = mp.Process(target=sensors_loop, args=(sensor_flags,))

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
