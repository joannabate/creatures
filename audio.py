from midi import MidiController
import numpy as np
import pandas as pd
from random import randrange, randint

class Audio:
    def __init__(self, df):
        self.controller = MidiController()
        self.df = df

        #Populate samples
        self.df_samples = self.generate_samples()
        self.ambient_sample = randint(0, 3)

    def generate_samples(self):
        # Create array to hold data
        sample_values = np.array([[np.NaN] * 12] * 6)

        # Populate drum loops
        for n in range(0,2):
            sample_values[n][randrange(2*n, 2*n + 2)] = randrange(6)

        # Pick a key for the samples
        key = randrange(7)

        # Populate samples
        for n in range(2,6):
            # Pick A or B and assign a sample
            sample_values[n][randrange(2*n, 2*n + 2)] = key

        # Shuffle rows
        np.random.shuffle(sample_values)

        # We start at midday, then make changes every 32 bars from (roughly) 7pm to 3am
        # Subtrct four so that we trigger a sample a beat before it needs to start
        ts = [x - 4 for x in [720, 1104, 1232, 1360, 48, 176]]
        cols = list(range(0, 111, 10))

        # Convert array to dataframe
        df_samples = pd.DataFrame(data=sample_values, index=ts, columns=cols)

        # Forward fill
        df_samples.ffill(inplace=True)

        # Set missing values to 8 (stop command)
        df_samples.fillna(8, inplace=True)

        # Create another dataframe to hold the fills. These occur 16 beats before each change.
        df_fills = df_samples.copy()
        df_fills.index = [x - 4 - 16 for x in [1104, 1232, 1360, 48, 176, 720]]
        
        # If there is a drum sample on the next row use a random fill value
        # Note that there is no fill added before the midday row - this is fine
        for i in range(5):
            index = df_fills.index[i]
            next_index = df_fills.index[i+1]
            for col in range(0, 40, 10):
                if df_fills.at[next_index, col] != 8:
                    df_fills.at[index, col] = randint(6,7)

        # Add fills back to samples dataframe
        df_samples = df_samples.append(df_fills)

        # Sort on timestep
        df_samples.sort_index(inplace=True)

        # Duplicate last row and set to midnight
        last_row = pd.DataFrame(df_samples[-1:].values, index=[0], columns=df_samples.columns)
        df_samples = df_samples.append(last_row)

        # Sort again
        df_samples.sort_index(inplace=True)

        # Convert to int and return
        return df_samples.astype('int')

    def run(self, i):
        # start playback
        self.controller.play_note(channel=0, note=100)

        i_last = -1
        ambient_vol_last = -1
        df_samples_last = self.df_samples.head(1).copy()
        ambient_sample_last = -1

        for col in df_samples_last.columns:
            df_samples_last[col].values[:] = 0

        while True:
            if i.value != i_last: # timestep has changed
                row = self.df.iloc[i.value]

                ambient_vol = int(row['Direct Beam'] * 127)

                if self.ambient_sample != ambient_sample_last:
                    for sample_bank in range(0, 20, 10):
                        self.controller.play_note(channel=0, note=sample_bank+self.ambient_sample)
                        ambient_sample_last = self.ambient_sample

                if ambient_vol != ambient_vol_last:
                    for cc in range(2):
                        self.controller.set_control(control=cc, value=ambient_vol)
                    print("setting ambient volume to " + str(ambient_vol))

                    for cc in range(2, 4):
                        self.controller.set_control(control=cc, value=(127-ambient_vol))
                    print("setting music volume to " + str(127-ambient_vol))

                # Get index for hour of day
                day_idx = i.value % 1440

                # Get current sample status
                df_samples_now = self.df_samples[self.df_samples.index <= day_idx].tail(1)

                # Activate new samples
                for sample_bank, sample in df_samples_now.items():
                    note = sample_bank + sample.values[0]
                    last_note = sample_bank + df_samples_last[sample_bank].values[0]
                    if note != last_note:
                        self.controller.play_note(channel=1, note=note)
                        print("sending note " + str(note))

                # If we're just before midday, regenerate samples
                if day_idx == (12*60 - 4 - 4):
                    self.df_samples = self.generate_samples()

                # If we're just before midnight, pick new ambient sample
                if day_idx == (24*60 - 4 - 4):
                    self.ambient_sample = randint(0, 3)

                i_last = i.value
                ambient_vol_last = ambient_vol
                df_samples_last = df_samples_now.copy()

if __name__ == "__main__":
    audio = Audio(None)
    print(audio.df_samples)