from platypush.context import get_plugin


class Devices:
    def __init__(self, df):
        self.df = df
        self.bulb_names = ['Bulb ' + str(n+1) for n in range(6)]
        self.plug_name = 'Plug'

    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = green[0] + (num * x_scale)
        y = green[1] + (num * y_scale)

        return {'x':x, 'y':y}
            
    def update_bulbs_brightness(self, value, sensor_flags):

        # Always update 5 and 6
        for s in (5,6):
            bulb_name = 'Bulb ' + str(s)

            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)

        # Update bulbs 1-4
        for s in range(4):
            bulb_name = 'Bulb ' + str(s+1)

            # If we have sensors and those sensors are off, set brightnes to 0
            if sensor_flags is not None:
                if not sensor_flags[s].value:
                    value = 0
            
            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)


    def update_bulbs_color(self, value):

        # Update bulbs 1-6
        for s in range(6):
            bulb_name = 'Bulb ' + str(s+1)
            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='color', value=value)

    def toggle_plug(self, value):
        get_plugin('zigbee.mqtt').device_set(device=self.plug_name, property='state', value=value)
        
    def run(self, i, sensor_flags):
        i_last = -1
        last_color = -1
        last_brightness = -1
        last_plug_state = 'Unknown'

        while True:
            if i.value != i_last: # timestep has changed

                row = self.df.iloc[i.value]
                color = self.convert_to_color(row['Direct Beam'])
                brightness = int(126 * row['Brightness'] + 128)
                plug_state = 'ON' if row['Direct Beam'] < 0.25 else 'OFF'

                if color != last_color:
                    # print('setting color to ' + str(color))
                    self.update_bulbs_color(color)
                if brightness != last_brightness:
                    # print('setting brightness to ' + str(brightness))
                    self.update_bulbs_brightness(brightness, sensor_flags)
                if plug_state != last_plug_state:
                    print('setting plug state to ' + plug_state)
                    self.toggle_plug(plug_state)

                i_last = i.value
                last_color = color
                last_brightness = brightness
                last_plug_state = plug_state