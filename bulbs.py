import time
from kasa import Discover, SmartBulb
import asyncio

class Bulbs:
    def __init__(self):
        self.bulbs = []

    async def get_bulbs(self):
        while True:
            devices = await Discover.discover()

            for addr, dev in devices.items():
                self.bulbs.append(SmartBulb(addr))
                print(f"{addr} >> {dev}")
            if len(self.bulbs) == 0:
                print('No bulbs discovered, retrying...')
            else:
                return
            
    async def update_bulb(self, bulb):
        await bulb.update()
        await bulb.set_hsv(c[0], c[1], c[2])
        await bulb.update()
        
    async def run(self, color_id):
        c_id = -1
        while True:
            if color_id.value != c_id: # emotion has changed
                await asyncio.gather(*(self.update_bulb(bulb, color_id) for bulb in self.bulbs))
                c_id = color_id.value 
            time.sleep(0.1)