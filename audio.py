from midi import MidiController

class Audio:
    def __init__(self, df):
        self.controller = MidiController()
        self.df = df

    def run(self, i):
        i_last = -1
        last_ambient_vol = -1

        while True:
            if i.value != i_last: # timestep has changed
                row = self.df.iloc[i.value]

                ambient_vol = int(row['Direct Beam'] * 127)

                if ambient_vol != last_ambient_vol:
                    self.controller.set_control(control=0, value=ambient_vol)
                    self.controller.set_control(control=1, value=ambient_vol)
                    print("setting ambient volume to " + str(ambient_vol))

                    self.controller.set_control(control=2, value=(127-ambient_vol))
                    self.controller.set_control(control=3, value=(127-ambient_vol))
                    print("setting music volume to " + str(127-ambient_vol))

                timestep = i.value % 1440

                i_last = i.value
                last_ambient_vol = ambient_vol