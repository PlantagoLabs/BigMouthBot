import threading
from queue import Queue
import asyncio
import json
import time
from datetime import datetime

from multiqueue import multiqueue

class BMBLinkClient:
    def __init__(self, ip, port, record = False):
        self.running = False
        self.incoming_queue, self.outgoing_queue = multiqueue.get_queues()
        self.ip = ip
        self.port = port
        self.connection = threading.Thread(target=self._run_connection).start()
        if record:
            self.record_file = open(f'recordings/recording_{datetime.now().isoformat()}.txt', 'w')
        else:
            self.record_file = None

    def _run_connection(self):
        asyncio.run(self.connect())

    async def connect(self):
        self.running = True
        print('trying to connect')
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        print('connected')
        self.receiver_task = asyncio.create_task(self._receive_data())
        self.send_task = asyncio.create_task(self._send_data())
        while self.running:
            await asyncio.sleep(0.01)
        self.receiver_task.cancel()
        self.send_task.cancel()

    def stop(self):
        self.running = False

    async def _receive_data(self):
        while 1:
            line = await self.reader.readline()
            try:
                data = json.loads(line)
                data['timestamp'] = time.time()
                self.incoming_queue.put(data)
            except:
                print(line)

            if self.record_file:
                self.record_file.write(json.dumps(data) + '\n')

    async def _send_data(self):
        while 1:
            while not self.outgoing_queue.empty():
                message = self.outgoing_queue.get()
                json_msg = (json.dumps(message)+'\n').encode()
                self.writer.write(json_msg)
                await self.writer.drain()
            await asyncio.sleep(0.01)