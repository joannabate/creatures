Code for "Elsewhen" project at TTITW

Setup follows https://hackernoon.com/how-to-transform-a-raspberrypi-into-a-universal-zigbee-and-z-wave-bridge-xy1ay3ymz

Sensors built following: https://community.home-assistant.io/t/diy-zigbee-bed-chair-occupancy-sensor/239517

To start services:

brew services restart mosquitto 

brew services restart redis

cd Desktop/zigbee2mqtt

conda deactivate

source bin/activate 

npm start

Zigbee UI at http://0.0.0.0:8080/

Platypush UI at http://127.0.0.1:8008/

To run script:

Create conda environement from requirements.txt, then run main.py from that environment
