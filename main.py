from time import time
import mido
import multiprocessing as mp
from devices import Devices
from data import load_data, get_start_index
from audio import Audio
# from video import Video
from sensors import Sensors
import asyncio
import multiprocessing as mp

class Clock:
    def __init__(self, start_index):
        self.inport = mido.open_input()
        self.i = start_index

    async def run(self, queue):
        ticks = 0
        print('Ready for midi...')

        message = {"source": "clock",
                    "payload": self.i}
        await queue.put(message)
        # print(f"Clock: {message}")
        await asyncio.sleep(0.001)

        for msg in self.inport:
            if msg.type == 'clock':
                    if ticks % 6 == 0:
                        # Loop round at end of day
                        self.i = (self.i + 1) % 525600
                        message = {"source": "clock",
                                   "payload": self.i}
                        await queue.put(message)
                        # print(f"Clock: {message}")
                        await asyncio.sleep(0.001)
                    ticks = ticks + 1


async def clock_loop(queue, start_index):
    my_clock = Clock(start_index)
    await my_clock.run(queue)

async def devices_loop(queue, df, sensor_flags):
    my_devices = Devices(df)
    await my_devices.run(queue, sensor_flags)

async def audio_loop(queue, df, sensor_flags):
    my_audio = Audio(df)
    await my_audio.run(queue, sensor_flags)

async def sensors_loop(queue, sensor_flags):
    my_sensors = Sensors()
    await my_sensors.run(queue, sensor_flags)

async def main():
    df = load_data(cached=True)
    start_index = get_start_index(df)

    s1 = mp.Value('b', False)
    s2 = mp.Value('b', False)
    s3 = mp.Value('b', False)
    s4 = mp.Value('b', False)
    s5 = mp.Value('b', False)
    s6 = mp.Value('b', False)

    sensor_flags = [s1, s2, s3, s4, s5, s6]
    # sensor_flags = None

    queue = asyncio.Queue()
    clock_task = asyncio.create_task(clock_loop(queue, start_index))
    devices_task = asyncio.create_task(devices_loop(queue, df, sensor_flags))
    sensors_task = asyncio.create_task(sensors_loop(queue, sensor_flags))
    audio_task = asyncio.create_task(audio_loop(queue, df, sensor_flags))

    await asyncio.gather(clock_task, devices_task, sensors_task, audio_task)

if __name__ == "__main__":
    asyncio.run(main())
