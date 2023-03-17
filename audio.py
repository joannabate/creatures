from midi import MidiController
import numpy as np
import pandas as pd
from random import randrange

class Audio:
    def __init__(self, df):
        self.controller = MidiController()
        self.df = df

        #Populate samples
        self.df_samples = self.generate_samples()

    def generate_samples(self):
        # Create array to hold data
        sample_values = np.array([[np.NaN] * 6] * 6)

        # Pick an Drums A sound
        sample_values[0][0] = randrange(8)

        # Pick an Drums B sound
        sample_values[1][1] = randrange(8)

        # Pick a key for the samples
        key = randrange(8)

        # Populate samples A through D
        for s in range(2,6):
            sample_values[s][s] = key

        # Shuffle rows
        np.random.shuffle(sample_values)

        # We make changes every two hours from 8pm to 4am
        ts = [60 * x - 5 for x in [20, 22, 2, 4]]

        # Add in midday
        ts.insert(0, 12*60 - 5)

        # Add in midnight
        ts.insert(-2, 0)

        # Convert array to dataframe
        df_samples = pd.DataFrame(data=sample_values,
                                  index=ts,
                                  columns=list(range(20, 71, 10)))

        # Forward fill
        df_samples.ffill(inplace=True)

        # Set missing values to 8 (stop command)
        df_samples.fillna(8, inplace=True)

        # Sort on timestep
        df_samples.sort_index(inplace=True)

        # Convert to int and return
        return df_samples.astype('int')

    def run(self, i):
        # start playback
        self.controller.play_note(channel=0, note=100)

        i_last = -1
        last_ambient_vol = -1

        df_samples_last = self.df_samples.head(1)
        for col in df_samples_last.columns:
            df_samples_last[col].values[:] = 0

        while True:
            if i.value != i_last: # timestep has changed
                row = self.df.iloc[i.value]

                ambient_vol = int(row['Direct Beam'] * 127)

                if ambient_vol != last_ambient_vol:
                    for cc in range(2):
                        self.controller.set_control(control=cc, value=ambient_vol)
                    print("setting ambient volume to " + str(ambient_vol))

                    for cc in range(2, 6):
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
                        self.controller.play_note(note=note)
                        print("sendind note " + str(note))

                # If we're at midday, regenerate samples
                if day_idx == 715:
                    self.df_samples = self.generate_samples()

                i_last = i.value
                last_ambient_vol = ambient_vol
                df_samples_last = df_samples_now.copy()

