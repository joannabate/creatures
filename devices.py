# from platypush.context import get_plugin
import aiomqtt
import json

N_BULBS = 7
N_PLUGS = 1
N_LIGHT_STRIPS = 1
N_SENSORS = 6

class Devices:
    def __init__(self, df):
        self.df = df

        # if sensors:
        #     self.sensor_flags = [False, False, False, False, False, False]
        # else:
        #     self.sensor_flags = [True, True, True, True, True, True]

    def convert_to_color(self, num):
        red = 0.7539, 0.2746
        green = 0.0771, 0.8268

        x_scale = red[0] - green[0]
        y_scale = red[1] - green[1]

        x = red[0] - (num * x_scale)
        y = red[1] - (num * y_scale)

        return {'x':x, 'y':y}
            
    async def update_bulbs_brightness(self, client, brightness, sensor_flags):
        # Always update 7 thru 10
        for s in (range(max(N_BULBS-N_SENSORS, 0))):
            bulb_name = 'Bulb ' + str(s+7)

            await client.publish(
                f"zigbee2mqtt/{bulb_name}/set",
                json.dumps(
                    {
                        "brightness": brightness,
                    }
                ),
            )

            # print('Setting ' + bulb_name + ' brightness to ' + str(value))
            # get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)

        # Always update light strips
        for s in range(N_LIGHT_STRIPS):
            # print('Setting Light Strip brightness to ' + str(value))
            # get_plugin('zigbee.mqtt').device_set(device='Light Strip ' + str(s+1), property='brightness', value=value)

            strip_name = 'Light Strip ' + str(s+1)

            await client.publish(
                f"zigbee2mqtt/{strip_name}/set",
                json.dumps(
                    {
                        "brightness": brightness,
                    }
                ),
            )

        # Update bulbs 1-6
        for s in range(min(N_BULBS, N_SENSORS)):
            bulb_name = 'Bulb ' + str(s+1)

            # If we have sensors and those sensors are on, set brightness
            if sensor_flags is not None:
                if sensor_flags[s].value == 1:
                    # print('Setting ' + bulb_name + ' brightness to ' + str(brightness))

                    await client.publish(
                        f"zigbee2mqtt/{bulb_name}/set",
                        json.dumps(
                            {
                                "brightness": brightness,
                            }
                        ),
                    )

                    # get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)
                else:
                    # print('Setting ' + bulb_name + ' brightness to 0')

                    await client.publish(
                        f"zigbee2mqtt/{bulb_name}/set",
                        json.dumps(
                            {
                                "brightness": 0,
                            }
                        ),
                    )

                    # get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=0)
            else:
                # If no sensors, always set brightness
                # print('Setting ' + bulb_name + ' brightness to ' + str(value))

                await client.publish(
                    f"zigbee2mqtt/{bulb_name}/set",
                    json.dumps(
                        {
                            "brightness": brightness,
                        }
                    ),
                )
                # get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=value)

    async def update_bulbs_color(self, client, color):
        # Update bulbs 1-10
        for s in range(N_BULBS):
            bulb_name = 'Bulb ' + str(s+1)

            await client.publish(
                f"zigbee2mqtt/{bulb_name}/set",
                json.dumps(
                    {
                        "color": color,
                    }
                ),
            )

            # print('Setting ' + bulb_name + ' color to ' + str(value))
            # await get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='color', value=value)

        # Always update light strips
        for s in range(N_LIGHT_STRIPS):
            # print('Setting Light Strip brightness to ' + str(value))

            strip_name = 'Light Strip ' + str(s+1)

            await client.publish(
                f"zigbee2mqtt/{strip_name}/set",
                json.dumps(
                    {
                        "color": color,
                    }
                ),
            )

            # await get_plugin('zigbee.mqtt').device_set(device='Light Strip ' + str(s+1), property='color', value=value)

        # Update light strip
        # for s in range(N_LIGHT_STRIPS):
        #     bulb_name = 'Light Strip' + str(s+1)
        #     print('Setting Light Strip color to ' + str(value))
        #     get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='color', value=value)

    async def toggle_plugs(self, client, state):
        for s in range(N_PLUGS):
            plug_name = 'Plug ' + str(s+1)

            await client.publish(
                f"zigbee2mqtt/{plug_name}/set",
                json.dumps(
                    {
                        "state": state,
                    }
                ),
            )

            # get_plugin('zigbee.mqtt').device_set(device=plug_name, property='state', value=value)
        
    async def run(self, queue, sensor_flags):

        last_color = {"x": 0, "y": 0}
        last_brightness = -1
        last_plug_state = 'Unknown'

        async with aiomqtt.Client("localhost") as client:
            while True:
                item = await queue.get()
                # print(f"Consumed: {item}")
                if item["source"] == "clock":
                    # print(sensor_flags)
                    row = self.df.iloc[item["payload"]]
                
                    color = self.convert_to_color(row['Direct Beam'])
                    brightness = int(126 * row['Brightness'] + 128)
                    plug_state = 'ON' if row['Direct Beam'] < 0.25 else 'OFF'

                    color_changed = (round(color['x'], 1) != round(last_color['x'], 1)) or (round(color['y'], 1) != round(last_color['y'], 1))
                    brightness_changed = int(brightness/10) != int(last_brightness/10)

                    try:
                        if color_changed:
                            print('setting color to ' + str(color))
                            await self.update_bulbs_color(client, color)
                        if brightness_changed:
                            print('setting brightness to ' + str(brightness))
                            await self.update_bulbs_brightness(client, brightness, sensor_flags)
                        if plug_state != last_plug_state:
                            print('setting plug state to ' + plug_state)
                            await self.toggle_plugs(client, plug_state)
                    except Exception as e:
                        print("WARNING: Devices failed to update")
                        print(e)
                        continue


                    last_color = color
                    last_brightness = brightness
                    last_plug_state = plug_state

                elif item["source"] == "sensors":
                    print(item)
                    sensor_id = int(item["payload"]["sensor_name"][-1]) - 1

                    bulb_name = 'Bulb ' + str(sensor_id + 1)
                    # If the sensor is on, switch bulb on

                    sensor_state = item["payload"]["state"]

                    try:
                        # await self.update_bulbs_brightness(client, brightness, sensor_flags)

                        if sensor_state:
                            print('Setting ' + bulb_name + ' brightness to ' + str(last_brightness))
                            await client.publish(
                                f"zigbee2mqtt/{bulb_name}/set",
                                json.dumps(
                                    {
                                        "brightness": last_brightness,
                                    }
                                ),
                            )

                        #     # get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=brightness)
                        else:
                            # Switch bulb off
                            # print('Setting ' + bulb_name + ' brightness to 0')

                            await client.publish(
                                f"zigbee2mqtt/{bulb_name}/set",
                                json.dumps(
                                    {
                                        "brightness": 0,
                                    }
                                ),
                            )
                        #     get_plugin('zigbee.mqtt').device_set(device=bulb_name, property='brightness', value=0)

                    except Exception as e:
                        print("WARNING: Devices failed to update")
                        print(e)
                        continue

                    




                queue.task_done()

