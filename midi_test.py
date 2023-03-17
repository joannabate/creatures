# import mido
# from time import sleep
# from random import randint

# outport = mido.open_output('IAC Driver creatures')

# middleC = 60

# while True:
#     msg = mido.Message('note_on', note=middleC, velocity=64)
#     outport.send(msg)
#     sleep(.5)

#     msg = mido.Message('control_change', control=2, value=randint(1,100))
#     outport.send(msg)
#     sleep(.5)

#     msg = mido.Message('note_off', note=middleC, velocity=64)
#     outport.send(msg)
#     sleep(.5) 


import mido
from time import sleep
from random import randint
from datetime import datetime

inport = mido.open_input()

for msg in inport:
    # print(msg.type)
    print(str(datetime.now()) + ' '+ str(msg))






