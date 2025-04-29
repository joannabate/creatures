import aiomqtt
import json

class Sensors:
    def __init__(self):
        self.sensor_names = [('zigbee2mqtt/Pressure 1', 0),
                             ('zigbee2mqtt/Pressure 2', 0),
                             ('zigbee2mqtt/Pressure 3', 0),
                             ('zigbee2mqtt/Pressure 4', 0),
                             ('zigbee2mqtt/Pressure 5', 0),
                             ('zigbee2mqtt/Pressure 6', 0)]

    async def run(self, queue, sensor_flags):
        async with aiomqtt.Client('localhost') as client:
            await client.subscribe(self.sensor_names)
            async for message in client.messages:

                response = json.loads(message.payload)
                topic = str(message.topic)

                sensor_name = topic.split("/")[-1]

                sensor_id = int(sensor_name[-1])-1

                state = response['contact']

                print(sensor_name + ' is ' + str(state))

                # Set sensor flags
                sensor_flags[sensor_id].value = state

                # Set sensor flag to response (true/false)
                message_out = {"source": "sensors",
                            "payload": {"sensor_name": sensor_name,
                                        "state": state}}
                
                # Inform other processes that sensor flags have changed
                await queue.put(message_out)
                # print(f"Sensor: {message_out}")
