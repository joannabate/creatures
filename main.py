import pandas as pd
from datetime import datetime
from time import time, sleep
import mido
import multiprocessing as mp
import asyncio
import random
from platypush.context import get_plugin

def data_loop(timestamp):
    my_data_loop = Data()
    my_data_loop.run(timestamp)

def bulb_loop(timestamp):
    my_bulbs = Bulbs() 
    asyncio.run(my_bulbs.get_bulbs())
    asyncio.run(my_bulbs.run(timestamp))

#One 15 min datapoint = 1 bar (approx 97bpm)
BPM = (365*24*4*4)/(24*60)
TEMPO = mido.bpm2tempo(BPM)

SECONDS_IN_DAY = 86400
SECONDS_IN_YEAR = 31536000
FIRST_TIMESTAMP = 1640167200
DATA_INTERVAL = 900
MIDDLE_C = 60

class Audio:
    def __init__(self):
        self.outport = mido.open_output('IAC Driver creatures')
        self.middleC = 60

        msg = mido.Message('note_off', note=middleC, velocity=64)
        outport.send(msg)
        msg = mido.Message('note_on', note=middleC, velocity=64)
        outport.send(msg)
        print('beat')

        for i, val in row.items():
            if i == 0:
                cc_value = int(val*128)
            else:
                cc_value = int((1-val)*128)
            msg = mido.Message('control_change', control=i, value=cc_value)
            outport.send(msg)
            print("Setting control signal %i to %i" % (i, cc_value))
            if i == 2:
                break


class Data:
    def __init__(self):

        self.df = pd.read_csv('power_data.csv', index_col=0)
        self.df['timestamp'] = pd.to_datetime(self.df.index, unit='s', utc=True).tz_convert("US/Hawaii")
        self.df['date'] = self.df['timestamp'].dt.date
        self.df['hour'] = self.df['timestamp'].dt.hour

        self.df[['power.ams_solar', 'power.pre_battery_grid', 'power.grid']
            ] = self.df.groupby(['service_account', 'date'])[
                'power.ams_solar', 'power.pre_battery_grid', 'power.grid'].apply(
                    lambda x: (x - x.min())/(x.max() - x.min()))

        self.dfs = {}
        for col in ['power.ams_solar', 'power.pre_battery_grid', 'power.grid']:
            self.dfs[col] = self.df.pivot(index=['date', 'hour', 'timestamp'], columns='service_account', values=col).reset_index()


        # Setup audio
        self.outport = mido.open_output('IAC Driver creatures')

    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = green[0] + (num * x_scale)
        y = green[1] + (num * y_scale)

        return {'x':x, 'y':y}

    def get_current_timestamp(self, tz_offset=-7):
        # Returns the timestep of the timeseries data based on current time of day
        local_time = ((time() + (tz_offset * 60 * 60)) % SECONDS_IN_DAY)
        current_timestamp = FIRST_TIMESTAMP + SECONDS_IN_YEAR * local_time/SECONDS_IN_DAY
        current_timestamp = DATA_INTERVAL * int(current_timestamp/DATA_INTERVAL)
        return current_timestamp

    def run(self, current_timestamp):

        starttime = time()

        hour = -1

        while True:
            for i, row in self.dfs['power.ams_solar'].iterrows():
                print(row[0])

                msg = mido.Message('note_on', note=MIDDLE_C, velocity=64)
                self.outport.send(msg)

                cc_value = random.randint(1,100)

                msg = mido.Message('control_change', control=1, value=cc_value)
                self.outport.send(msg)
                print("Setting control signal %i to %i" % (1, cc_value))

                msg = mido.Message('note_off', note=MIDDLE_C, velocity=64)
                self.outport.send(msg)

                color_1 = self.convert_to_color(row[0])
                color_2 = self.convert_to_color(row[1])
                print(row[0])
                print(row[1])
                if row['hour'] != hour:
                    hour = row['hour']
                    try:
                        get_plugin('zigbee.mqtt').device_set(device='Bulb 1', property='color', value=color_1)
                        get_plugin('zigbee.mqtt').device_set(device='Bulb 2', property='color', value=color_2)
                        print('Setting Bulb 1 to %f', color_1)
                        print('Setting Bulb 2 to %f', color_2)

                    except:
                        continue

                # Sleep until the next beat
                sleep((TEMPO - ((time() - starttime) % TEMPO))/1000000.0)


if __name__ == "__main__":
    
    # mp.set_start_method('forkserver')


    
    current_timestamp = mp.Value('i', 0)

    my_data_loop = Data()
    my_data_loop.run(current_timestamp)
    
    # p1 = mp.Process(target=data_loop, args=(current_timestamp, ))
#    p2 = mp.Process(target=bulb_loop, args=(current_timestamp, ))
    
    # p1.start()
#    p2.start()

    # p1.join()
#    p2.join()
