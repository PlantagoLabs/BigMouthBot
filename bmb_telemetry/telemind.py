from threading import Thread
import time
import asyncio

async def sleep_ms(duration):
    await asyncio.sleep(duration/1000.)

asyncio.sleep_ms = sleep_ms

from multiqueue import multiqueue

import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/../firmware/lib/BMBLib")
print(sys.path)

import synapse

import numpy as np

print(dir(synapse))

def print_high_gryo_data(topic, message, source):
    if message['gyro'][0] > 0.2:
        print(message)

async def main_task():
    synapse.subscribe('imu', print_high_gryo_data)
    while 1:
        print('in main task loop')
        await asyncio.sleep_ms(1000)

class BasicGridSLAM:
    def __init__(self):
        self.measurement_grid = np.ones([2000, 2000])
        self.pose = None

    async def corun(self):
        while 1:
            print('in main task loop')
            await asyncio.sleep_ms(1000)

    def _save_pose(self, topic, message, source):
        self.pose = np.array([message['x'], message['y'], message['heading']])
        print(self.pose)

    def _process_range_array(self, topic, message, source):
        
        synapse.publish('map', {self.measurement_grid})

class TeleMind:
    def __init__(self, main_task):
        self.outgoing_queue, self.incoming_queue = multiqueue.get_queues()
        self.main_task = main_task
        self.running = True
        self.thread = Thread(target=self.__run).start()

    def __run(self):
        asyncio.run(self.__loop())

    async def __loop(self):
        asyncio.create_task(self.main_task())
        asyncio.create_task(self.__process_incoming())
        for outgoing_topic in self.outgoing_topics:
            synapse.subscribe(outgoing_topic, self.__process_outgoing)
        while self.running:
            await asyncio.sleep(1)

    async def __process_incoming(self):
        while self.running:
            if not self.incoming_queue.empty():
                message = self.incoming_queue.get()
                synapse.publish(message['topic'], message['message'], message['source'])
            await asyncio.sleep(0.001)

    def __process_outgoing(self, topic, message, source):
        self.outgoing_queue.put({'topic': topic, 'message': message, 'source': source, 'internal': topic not in self.outgoing_topics})

