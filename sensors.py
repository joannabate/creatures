from urllib.parse import urlparse
import paho.mqtt.client as mosquitto
import json
from time import sleep
import multiprocessing as mp

# Define event callbacks
class Sensors:
    def __init__(self):
        self.url_str = 'mqtt://localhost:1883'
        self.sensor_names = [('zigbee2mqtt/Sensor 1', 0),
                             ('zigbee2mqtt/Sensor 2', 0),
                             ('zigbee2mqtt/Sensor 3', 0),
                             ('zigbee2mqtt/Sensor 4', 0),
                             ('zigbee2mqtt/Sensor 5', 0),
                             ('zigbee2mqtt/Sensor 6', 0)]

    def on_connect(self, mosq, obj, flag, rc):
        print("rc: " + str(rc))

    def on_message(self, mosq, sensor_flags, msg):
        # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        response = json.loads(msg.payload)
        sensor_id = int(msg.topic[-1])

        print('sensor ' + str(sensor_id) + ' is ' + str(response['contact']))

        # Set sensor flag to response (true/false)
        if sensor_flags is not None:
            sensor_flags[sensor_id-1].value = response['contact']

    def on_publish(self, mosq, obj, mid):
        # print("Publish: " + str(mid))
        return

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        # print("Subscribed: " + str(mid))
        return

    def on_log(self, mosq, obj, level, string):
        # print(" Log: " + string)
        return

    def run(self, sensors):

        mqttc = mosquitto.Client(userdata=(sensors))

        # Assign event callbacks
        mqttc.on_message = self.on_message
        mqttc.on_connect = self.on_connect
        mqttc.on_publish = self.on_publish
        mqttc.on_subscribe = self.on_subscribe

        # Uncomment to enable debug messages
        mqttc.on_log = self.on_log

        # Parse CLOUDAMQP_MQTT_URL (or fallback to localhost)
        url = urlparse(self.url_str)

        # Connect
        mqttc.username_pw_set(url.username, url.password)
        mqttc.connect(url.hostname, url.port)

        # Start subscribe, with QoS level 0
        mqttc.subscribe(self.sensor_names, 0)

        # Publish a message
        # mqttc.publish("hello/world", "my message")

        # Continue the network loop, exit when an error occurs
        rc = 0
        while rc == 0:
            rc = mqttc.loop()
        print("rc: " + str(rc))

if __name__ == "__main__":
    s1 = mp.Value('b', False)
    s2 = mp.Value('b', False)
    s3 = mp.Value('b', False)
    s4 = mp.Value('b', False)
    s5 = mp.Value('b', False)
    s6 = mp.Value('b', False)

    sensor_flags = [s1, s2, s3, s4, s5, s6]

    my_sensors = Sensors()
    my_sensors.run(sensor_flags)