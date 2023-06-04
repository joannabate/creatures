from midi import MidiController
import numpy as np
import pandas as pd
from random import randrange, randint, choice
from time import time

AMBIENT_CHANNEL = 0
MUSIC_CHANNEL = 1
RETURN_CHANNEL = 2

class Audio:
    def __init__(self, df):
        self.controller = MidiController()
        self.df = df

    def generate_samples(self, sensor_flags):
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

        # Split out the ambient samples
        ambient_sample_values = sample_values[-2:]
        sample_values = sample_values[:-2]

        # Shuffle rows
        np.random.shuffle(sample_values)
        np.random.shuffle(ambient_sample_values)

        # Concat back together
        sample_values = np.concatenate((ambient_sample_values, sample_values), axis=0)

        # We start at midday, then make changes every 32 bars from (roughly) 7pm to 3am
        # Subtrct four so that we trigger a sample a beat before it needs to start
        ts = [x - 4 for x in [720, 1104, 1232, 1360, 48, 176]]
        cols = list(range(0, 111, 10))

        # Convert array to dataframe
        df_samples = pd.DataFrame(data=sample_values, index=ts, columns=cols)

        # Record the order we're activating samples in
        self.sample_order = []
        for _, row in df_samples.iterrows():
            self.sample_order.append(row[row.notnull()].index[0])

        # Forward fill
        df_samples.ffill(inplace=True)

        # Set missing values to 8 (stop command)
        df_samples.fillna(8, inplace=True)

        # If there are sensors the samples are always ready to be played, if activated by a sensor
        # Otherwise a "song" is built with the samples triggering in a specific order
        # We hack this by setting all values to the last row (fully built song)
        if sensor_flags:
            df_samples.iloc[:,:] = df_samples.iloc[5,].values

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

        # Duplicate last row and set to midday
        last_row = pd.DataFrame(df_samples[-1:].values, index=[0], columns=df_samples.columns)
        df_samples = df_samples.append(last_row)

        # Sort again
        df_samples.sort_index(inplace=True)

        # Convert to int and return
        df_samples = df_samples.astype('int')
        print('NEW SAMPLES')
        print(df_samples)
        print('Sample order')
        print(self.sample_order)
        return df_samples
    
    def set_initial_music_settings(self):
        # Set first two ordered music samples to all speakers
        for n in range(2):
            sample_bank = self.sample_order[n]
            self.set_all_speakers(MUSIC_CHANNEL, sample_bank)

        # Set the other four to go to individual speakers
        for sensor_id in range(4):
            sample_bank = self.sample_order[sensor_id+2]
            self.set_solo_speaker(MUSIC_CHANNEL, sample_bank, sensor_id)

        # Set all other channels to off
        for sample_bank in range(0, 111, 10):
            if sample_bank not in self.sample_order:
                self.set_all_off(MUSIC_CHANNEL, sample_bank)

    def set_initial_ambient_settings(self):
        # Set fifth  amient sample to all speakers
        sample_bank = 40
        self.set_all_speakers(AMBIENT_CHANNEL, sample_bank)

        # Set the other four to go to individual speakers
        for sensor_id in range(4):
            sample_bank = sensor_id * 10
            self.set_solo_speaker(AMBIENT_CHANNEL, sample_bank, sensor_id)

    def set_all_speakers(self, channel, sample_bank):
        if channel == AMBIENT_CHANNEL:
            channel_name = 'Ambient'
            a_b_vol = 127
            c_d_vol = 0
        elif channel == MUSIC_CHANNEL:
            channel_name = 'Music'
            a_b_vol = 0
            c_d_vol = 127
        else:
            raise Exception("Channel not recognized")

        print(channel_name + ' Bank ' + str(sample_bank) + ' to all speakers')
        self.controller.set_control(channel, control=sample_bank, value=63)
        self.controller.set_control(channel, control=sample_bank+1, value=63)
        for send in range(2):
            self.controller.set_control(channel, control=sample_bank+2+send, value=a_b_vol)
            self.controller.set_control(channel, control=sample_bank+4+send, value=c_d_vol)

    def set_solo_speaker(self, channel, sample_bank, id):

        # Panning and send is determined by which speaker we want to hit
        # Speaker 1 (ID 0) = send A or C, hard left
        # Speaker 2 (ID 1) = send A or C, hard right
        # Speaker 3 (ID 2) = send B or D, hard left
        # Speaker 4 (ID 3) = send B or D, hard right

        # Pan is the same for both ambient and music
        if id in (0, 2):
            pan_value = 0
        else:
            pan_value = 127

        # Set pan and volume
        self.controller.set_control(channel=channel, control=sample_bank+1, value=pan_value)
        self.controller.set_control(channel, control=sample_bank, value=95)

        # Set to off if ambient and we have sensors, on otherwise
        if channel == AMBIENT_CHANNEL:
            print('Ambient Bank ' + str(sample_bank) + ' to solo speaker')
            # Set send to A or B
            if id in (0, 1):
                send_cc = 0 # Send A
            else:
                send_cc = 1 # Send B

        # Set to on if music
        elif channel == MUSIC_CHANNEL:
            print('Music Bank ' + str(sample_bank) + ' to solo speaker')
            # Set send to C or D
            if id in (0, 1):
                send_cc = 2 # Send C
            else:
                send_cc = 3 # Send D
        else:
            raise Exception("Channel not recognized")

        for send in range(4):
            # Set the send we want to on, set the rest to off
            if send == send_cc:
                self.controller.set_control(channel=channel, control=sample_bank+2+send, value=127)
            else:
                self.controller.set_control(channel=channel, control=sample_bank+2+send, value=0)

    def set_all_off(self, channel, sample_bank):
        print('Channel ' + str(channel) + ' Bank ' + str(sample_bank) + ' off')
        self.controller.set_control(channel=channel, control=sample_bank, value=0)
        self.controller.set_control(channel=channel, control=sample_bank+1, value=63)
        for send in range(4):
            self.controller.set_control(channel=channel, control=sample_bank+2+send, value=0)

    def run(self, i, sensor_flags):

        # Populate samples
        self.df_samples = self.generate_samples(sensor_flags)

        # start playback
        self.controller.play_note(RETURN_CHANNEL, note=100)

        i_last = -1
        ambient_vol_last = -1
        ambient_last = -1
        ambient = choice(range(0,5))
        
        if sensor_flags is not None:
            sensor_flags_last = [-1, -1, -1, -1]

        # Last samples data frame is a row with all samples set to -1
        df_samples_last = self.df_samples.head(1).copy()
        for col in df_samples_last.columns:
            df_samples_last[col].values[:] = -1

        self.set_initial_music_settings()
        self.set_initial_ambient_settings()

        while True:
            if i.value != i_last: # timestep has changed
                row = self.df.iloc[i.value]

                ambient_vol = int(row['Direct Beam'] * 95)

                if sensor_flags is not None:
                    # print('sensor_flags: ' + str([s.value for s in sensor_flags]))
                    # print('sensor_flags_last: ' + str(sensor_flags_last))
                    # For every sensor, 
                    for sensor_id in range(4):
                        # If the value has changed
                        # print('sensor_flags[' + str(sensor_id) + '].value: ' + str(sensor_flags[sensor_id].value))
                        # print('sensor_flags_last[' + str(sensor_id) + ']: ' + str(sensor_flags_last[sensor_id]))
                        if sensor_flags[sensor_id].value != sensor_flags_last[sensor_id]:

                            print('Processing sensor ' + str(sensor_id+1) + ' (' + str(sensor_flags[sensor_id].value) +')')
                            
                            # Set music volume on
                            sample_bank = self.sample_order[sensor_id+2]
                            print('Music Bank ' + str(sample_bank) + ' (' + str(sensor_flags[sensor_id].value) +')')
                            self.controller.set_control(MUSIC_CHANNEL, control=sample_bank, value=int(sensor_flags[sensor_id].value)*95)

                            # Set ambient volume on
                            # (Ambient banks are constant, no need to lookup)
                            sample_bank = sensor_id * 10
                            print('Ambient Bank ' + str(sample_bank) + ' (' + str(sensor_flags[sensor_id].value) +')')
                            self.controller.set_control(AMBIENT_CHANNEL, control=sample_bank, value=int(sensor_flags[sensor_id].value)*95)
                        
                            # Update last sensor flags
                            sensor_flags_last[sensor_id] = sensor_flags[sensor_id].value

                if ambient != ambient_last:
                    for sample_bank in range(0, 50, 10):
                        self.controller.play_note(AMBIENT_CHANNEL, note=sample_bank+ambient)
                    ambient_last = ambient

                if ambient_vol != ambient_vol_last:
                    for cc in range(2):
                        self.controller.set_control(RETURN_CHANNEL, control=cc, value=ambient_vol)
                    # print("setting ambient volume to " + str(ambient_vol))

                    for cc in range(2, 4):
                        self.controller.set_control(RETURN_CHANNEL, control=cc, value=(95-ambient_vol))
                    # print("setting music volume to " + str(127-ambient_vol))

                # Get index for hour of day
                day_idx = i.value % 1440

                # Get current sample status
                df_samples_now = self.df_samples[self.df_samples.index <= day_idx].tail(1)

                # Activate new samples
                for sample_bank, sample in df_samples_now.items():
                    note = sample_bank + sample.values[0]
                    last_note = sample_bank + df_samples_last[sample_bank].values[0]
                    if note != last_note:
                        self.controller.play_note(MUSIC_CHANNEL, note=note)
                        print("sending music note " + str(note))

                # If we're just before midday, regenerate music samples
                if day_idx == (12*60 - 4 - 4):
                    self.df_samples = self.generate_samples(sensor_flags)

                    # Reset sensor flags
                    if sensor_flags is not None:
                        sensor_flags_last = [-1, -1, -1, -1]

                    # Reset music settings for new samples
                    self.set_initial_music_settings()


                # If we're just before midnight, pick new ambient sample
                if day_idx == (24*60 - 4 - 4):
                    ambient = choice([i for i in range(0,5) if i != ambient])


                i_last = i.value
                ambient_vol_last = ambient_vol
                df_samples_last = df_samples_now.copy()

if __name__ == "__main__":
    audio = Audio(None)