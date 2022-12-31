import pandas as pd
from datetime import datetime
from time import time, sleep
import mido

#One 15 min datapoint = 1 bar (approx 97bpm)
BPM = (365*24*4*4)/(24*60)
TEMPO = mido.bpm2tempo(BPM)

df = pd.read_csv('data.csv', index_col=0)

# Convert index to integer (one per 15 minutes)
df.index = ((df.index - 1640995200)/900).astype('int')

# Subtract 10 hours to get to local time
df.index = (df.index - 40)%(365*24*4)
df['utc_timestamp'] = df.index

dfs = {}
for col in ['power.ams_solar', 'power.pre_battery_grid', 'power.grid']:
    # Pull out datapoints, normalize
    dfs[col] = df.pivot(index='utc_timestamp', columns='service_account', values=col)
    dfs[col] = (dfs[col] - dfs[col].min())/(dfs[col].max() - dfs[col].min())
    dfs[col].sort_index(inplace=True)

dfs['power.ams_solar'].to_clipboard()

current_index = 0

outport = mido.open_output('IAC Driver python')

middleC = 60

starttime = time()

while True:
    # msg = mido.Message('note_off', note=middleC, velocity=64)
    # outport.send(msg)
    # msg = mido.Message('note_on', note=middleC, velocity=64)
    # outport.send(msg)
    print('beat')
    # Get percent of way through current day and convert to same index as df
    now = datetime.now()
    new_index = int((365*24*4) * (now.hour*60*60 + now.minute*60 + now.second)/(24*60*60))

    # If time has advanced (or first run through)
    if new_index != current_index:
        current_index = new_index
        row = dfs['power.ams_solar'].iloc[current_index]

        i=1
        for _, val in row.items():
            if i == 1:
                cc_value = int(val*128)
            else:
                cc_value = int((1-val)*128)
            msg = mido.Message('control_change', control=i, value=cc_value)
            outport.send(msg)
            print("Setting control signal %i to %i" % (i, cc_value))
            i = i+1
            if i == 3:
                break

    # Sleep until the next beat
    sleep((TEMPO - ((time() - starttime) % TEMPO))/1000000.0)
