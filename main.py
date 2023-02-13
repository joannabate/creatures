import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
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
        self.df = self.process_data()
        
        # Setup audio
        self.outport = mido.open_output('IAC Driver creatures')

    def process_data(self):

        # Read in data and drop unecessary columns
        df = pd.read_csv('sunrise_sunset_times.csv')
        df.drop(columns=['Unnamed: 4', 'Daylength'], inplace=True)

        # Convert sunrise and sunset times to datetime objects in Pacfic winter time
        df['Sunrise'] = pd.to_datetime(df['Date'] + ' ' + df['Sunrise']).dt.tz_localize('US/Pacific').dt.tz_convert('Etc/GMT+8')
        df['Sunset'] = pd.to_datetime(df['Date'] + ' ' + df['Sunset']).dt.tz_localize('US/Pacific').dt.tz_convert('Etc/GMT+8')
        
        # Add in twilight start and end times
        df['Twilight Start'] = df['Sunrise'] - timedelta(hours=1, minutes=30)
        df['Twilight End'] = df['Sunset'] + timedelta(hours=1, minutes=30)

        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize('US/Pacific').dt.tz_convert('Etc/GMT+8')


        return df

    def get_data_start_time(self):

        start_time = datetime.now()
        decimal_time = int(start_time.hour)/24 + int(start_time.minute)/(24*60) + int(start_time.second)/(24*60*60)

        first_date = datetime(year=2022, month=12, day=21)
        data_duration = (365*24*60*60)

        data_start_time = first_date.timestamp() + (decimal_time * data_duration)

        return datetime.fromtimestamp(data_start_time, timezone('Etc/GMT+8'))


    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = green[0] + (num * x_scale)
        y = green[1] + (num * y_scale)

        return {'x':x, 'y':y}

    # def get_current_timestamp(self, tz_offset=-7):
    #     # Returns the timestep of the timeseries data based on current time of day
    #     local_time = ((time() + (tz_offset * 60 * 60)) % SECONDS_IN_DAY)
    #     current_timestamp = FIRST_TIMESTAMP + SECONDS_IN_YEAR * local_time/SECONDS_IN_DAY
    #     current_timestamp = DATA_INTERVAL * int(current_timestamp/DATA_INTERVAL)
    #     return current_timestamp

    def run(self, current_timestamp):

        # Setup time counters
        real_start_time = time()
        data_time = self.get_data_start_time()

        while True:
            for i, row in self.df.iterrows():
                # Skip forward to start of data
                if row['Date'].date() == data_time.date():
                    # We're on the right line for this date
                    while row['Date'].date() == data_time.date():
                        print(data_time)
                        # While this is still true...
                        if data_time < row['Twilight Start']:
                            # Before Twilight it is dark
                            val = 1
                        elif data_time < row['Sunrise']:
                            # Between twilight start and sunrise the sun is partially up
                            # Figure out how far we are past twilight
                            val = (row['Sunset'].timestamp() - data_time.timestamp()) / (60*90)

                        elif data_time < row['Sunset']:
                            # During the day it is light
                            val = 0

                        elif data_time < row['Twilight End']:
                            # Between sunset and twilight end the sun is partially up
                            # Figure out how far we are past twilight
                            val = (data_time.timestamp() - row['Sunset'].timestamp()) / (60*90)

                        else:
                            # After twilight end it is dark
                            val = 1

                        # Do stuff
                        msg = mido.Message('note_on', note=MIDDLE_C, velocity=64)
                        self.outport.send(msg)

                        cc_value = random.randint(1,100)

                        msg = mido.Message('control_change', control=1, value=cc_value)
                        self.outport.send(msg)
                        print("Setting control signal %i to %i" % (1, cc_value))

                        msg = mido.Message('note_off', note=MIDDLE_C, velocity=64)
                        self.outport.send(msg)

                        color = self.convert_to_color(val)
                        try:
                            get_plugin('zigbee.mqtt').device_set(device='Bulb 1', property='color', value=color)
                            get_plugin('zigbee.mqtt').device_set(device='Bulb 2', property='color', value=color)
                            print('Setting Bulb 1 to %f', color)
                            print('Setting Bulb 2 to %f', color)

                        except:
                            continue

                        # Advance data time
                        data_time = data_time + timedelta(minutes=15)

                        # Sleep until the next beat
                        sleep((TEMPO - ((time() - real_start_time) % TEMPO))/1000000.0)


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
