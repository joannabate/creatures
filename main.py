import pandas as pd
from datetime import datetime
from time import time, sleep
import mido
import multiprocessing as mp
import asyncio
import random
from platypush.context import get_plugin
from pytz import timezone
import numpy as np


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

        self.df = self.load_data()

        # Setup audio
        self.outport = mido.open_output('IAC Driver creatures')

    def load_data(self):
        df = pd.read_csv('irradiance.csv')

        df_mins = pd.DataFrame(data={'mins': range(60)})

        # Cross-join data to expand from hourly to 1 min
        df['key'] = 0
        df_mins['key'] = 0

        df = df.merge(df_mins, on='key', how='outer')

        df['Timestamp'] = pd.to_datetime(df['Timestamp']) + pd.to_timedelta(df['mins'], unit='m')

        df.drop(columns=['key', 'mins'], inplace=True)

        # Apply a rolling window and average. Data is reversed to get a forward looking average.
        df.loc[:, df.columns!='Timestamp'] = df.loc[:, df.columns!='Timestamp'][::-1].rolling(60, min_periods=1).mean()[::-1]

        # Normalize entire dataset between 1.5 and 0
        df.loc[:, df.columns!='Timestamp'] = df.loc[:, df.columns!='Timestamp'].apply(lambda x: 1.5 * (x - x.min())/(x.max() - x.min()))

        #Add some noise
        df['angle'] = 4 * (df.index % 90) * np.pi / 180
        df['Direct Beam'] = df['Direct Beam'] + df['angle'].apply(lambda x: (np.sin(x)+1)/5)

        # Normalize entire dataset between 1.5 and 0, then clip to 1
        df.loc[:, df.columns!='Timestamp'] = df.loc[:, df.columns!='Timestamp'].apply(lambda x: 1.5 * (x - x.min())/(x.max() - x.min())).clip(upper=1)


        return df


    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = green[0] + (num * x_scale)
        y = green[1] + (num * y_scale)

        return {'x':x, 'y':y}

    def get_data_start_time(self):

        start_time = datetime.now()
        decimal_time = int(start_time.hour)/24 + int(start_time.minute)/(24*60) + int(start_time.second)/(24*60*60)

        first_date = datetime(year=2022, month=12, day=21)
        data_duration = (365*24*60*60)

        data_start_time = first_date.timestamp() + (decimal_time * data_duration)

        return datetime.fromtimestamp(data_start_time, timezone('Etc/GMT+8'))


    def run(self, current_timestamp):

        # Setup time counters
        real_start_time = time()
        prev_color = -1

        # Filter to correct point in data based on time of day
        df = self.df[self.df['Timestamp']>np.datetime64(self.get_data_start_time())]

        while True:
            for i, row in df.iterrows():
                print(row['Timestamp'], row['Direct Beam'])

                msg = mido.Message('note_on', note=MIDDLE_C, velocity=64)
                self.outport.send(msg)

                cc_value = random.randint(1,100)

                msg = mido.Message('control_change', control=1, value=cc_value)
                self.outport.send(msg)
                print("Setting control signal %i to %i" % (1, cc_value))

                msg = mido.Message('note_off', note=MIDDLE_C, velocity=64)
                self.outport.send(msg)

                color = self.convert_to_color(row['Direct Beam'])

                if color != prev_color:
                    for n in range(2):
                        try:
                            bulb_name = 'Bulb ' + str(n+1)
                            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='color', value=color)
                            print('Setting %f to %f', bulb_name, color)
                            #sleep(0.2)

                        except:
                            continue

                prev_color = color

                # Sleep until the next beat
                sleep((TEMPO - ((time() - real_start_time) % TEMPO))/(15 * 1000000.0))
            
            # Next time round use full dataset
            df = self.df

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
