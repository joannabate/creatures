import pandas as pd
from datetime import datetime
from time import time, sleep
import mido
#from bulbs import Bulbs
import multiprocessing as mp
import asyncio


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

# class Audio:
#     def __init__(self):
#         self.outport = mido.open_output('IAC Driver creatures')
#         self.middleC = 60

#         msg = mido.Message('note_off', note=middleC, velocity=64)
#         outport.send(msg)
#         msg = mido.Message('note_on', note=middleC, velocity=64)
#         outport.send(msg)
#         print('beat')

#             for i, val in row.items():
#                 if i == 0:
#                     cc_value = int(val*128)
#                 else:
#                     cc_value = int((1-val)*128)
#                 msg = mido.Message('control_change', control=i, value=cc_value)
#                 outport.send(msg)
#                 print("Setting control signal %i to %i" % (i, cc_value))
#                 if i == 2:
#                     break

class Data:
    def __init__(self):
        self.df = pd.read_csv('power_data.csv', index_col=0)
        self.df['utc_timestamp'] = self.df.index

        self.dfs = {}
        for col in ['power.ams_solar', 'power.pre_battery_grid', 'power.grid']:
            # Pull out datapoints, normalize
            self.dfs[col] = self.df.pivot(index='utc_timestamp', columns='service_account', values=col)
            self.dfs[col] = (self.dfs[col] - self.dfs[col].min())/(self.dfs[col].max() - self.dfs[col].min())
            self.dfs[col].sort_index(inplace=True)

    def get_current_timestamp(self, tz_offset=-7):
        # Returns the timestep of the timeseries data based on current time of day
        local_time = ((time() + (tz_offset * 60 * 60)) % SECONDS_IN_DAY)
        current_timestamp = FIRST_TIMESTAMP + SECONDS_IN_YEAR * local_time/SECONDS_IN_DAY
        current_timestamp = DATA_INTERVAL * int(current_timestamp/DATA_INTERVAL)
        return current_timestamp

    def run(self, current_timestamp):

        starttime = time()

        while True:
            for i, row in self.dfs['power.ams_solar'].iterrows():
                print(row[0])

                # Sleep until the next beat
                sleep((TEMPO - ((time() - starttime) % TEMPO))/1000000.0)


if __name__ == "__main__":
    
    mp.set_start_method('forkserver')
    
    current_timestamp = mp.Value('i', 0)
    
    p1 = mp.Process(target=data_loop, args=(current_timestamp, ))
#    p2 = mp.Process(target=bulb_loop, args=(current_timestamp, ))
    
    p1.start()
#    p2.start()

    p1.join()
#    p2.join()
