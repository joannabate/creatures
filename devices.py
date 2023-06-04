from platypush.context import get_plugin


class Devices:
    def __init__(self, df):
        self.df = df
        self.bulb_names = ['Bulb ' + str(n+1) for n in range(10)]
        self.plug_name = 'Plug'

    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = red[0] - (num * x_scale)
        y = red[1] - (num * y_scale)

        return {'x':x, 'y':y}
            
    def update_bulbs_brightness(self, value, sensor_flags):

        # Always update 5 thru 10
        for s in (range(6)):
            bulb_name = 'Bulb ' + str(s+5)

            # print('Setting ' + bulb_name + ' brightness to ' + str(value))
            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)

        # Update bulbs 1-4
        for s in range(4):
            bulb_name = 'Bulb ' + str(s+1)

            # If we have sensors and those sensors are on, set brightness
            if sensor_flags is not None:
                if sensor_flags[s].value:
                    # print('Setting ' + bulb_name + ' brightness to ' + str(value))
                    get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)
                else:
                    # print('Setting ' + bulb_name + ' brightness to 0')
                    get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=0)
            else:
                # If no sensors, always set brightness
                # print('Setting ' + bulb_name + ' brightness to ' + str(value))
                get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)


    def update_bulbs_color(self, value):

        # Update bulbs 1-10
        for s in range(10):
            bulb_name = 'Bulb ' + str(s+1)
            # print('Setting ' + bulb_name + ' color to ' + str(value))
            get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='color', value=value)

    def toggle_plug(self, value):
        get_plugin('zigbee.mqtt').device_set(device=self.plug_name, property='state', value=value)
        
    def run(self, i, sensor_flags):
        i_last = -1
        last_color = -1
        last_brightness = -1
        last_plug_state = 'Unknown'

        if sensor_flags is not None:
            sensor_flags_last = [-1, -1, -1, -1]

        while True:
            if i.value != i_last: # timestep has changed

                row = self.df.iloc[i.value]
                color = self.convert_to_color(row['Direct Beam'])
                brightness = int(126 * row['Brightness'] + 128)
                plug_state = 'ON' if row['Direct Beam'] < 0.25 else 'OFF'

                if sensor_flags is not None:
                    sensor_flags_last = [-1, -1, -1, -1]

                try:
                    if color != last_color:
                        # print('setting color to ' + str(color))
                        self.update_bulbs_color(color)
                    if (brightness != last_brightness):
                        # print('setting brightness to ' + str(brightness))
                        self.update_bulbs_brightness(brightness, sensor_flags)
                    if plug_state != last_plug_state:
                        print('setting plug state to ' + plug_state)
                        self.toggle_plug(plug_state)
                except:
                    print("WARNING: Devices failed to update")
                    continue

                # If we have sensors
                if sensor_flags is not None:
                    # For every sensor, 
                    for sensor_id in range(4):
                        # If the value has changed
                        if sensor_flags[sensor_id].value != sensor_flags_last[sensor_id]:
                            bulb_name = 'Bulb ' + str(sensor_id+1)
                            # If the sensor is off
                            try:
                                if not sensor_flags[sensor_id].value:
                                    # Switch bulb off
                                    # print('Setting ' + bulb_name + ' brightness to 0')
                                    get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=0)
                                else:
                                    # Switch bulb on
                                    get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=brightness)
                            except:
                                print("WARNING: Devices failed to update")
                                continue
                        # Update last sensor flags
                        sensor_flags_last[sensor_id] = sensor_flags[sensor_id].value


                i_last = i.value
                last_color = color
                last_brightness = brightness
                last_plug_state = plug_state