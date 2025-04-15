import network
import asyncio
import json
from BMBLib import profiler

class BMBLink():
    def __init__(self):
        self.on_connection_msg = None

        self._latest_id = 0
        self._links = {}

    @profiler.profile("bmbnet.send")
    async def send_message(self, message):
        for link in self._links:
            self._links[link][1].write(message)
            await self._links[link][1].drain()

    def send_synaptic_mssage(self, topic, message, source):
        print(topic)
        full_msg = {'topic': topic, 'message': message, 'source': source}
        json_msg = (json.dumps(full_msg)+'\n').encode()
        asyncio.create_task(self.send_message(json_msg))
        
    async def handle_connection(self, reader, writer):
        print('connection !')
        self._links[self._latest_id] = (reader, writer)
        asyncio.create_task(self.read_from_connection(self._latest_id, reader))
        self._latest_id += 1
        if self.on_connection_msg:
            await self.send_message(self.on_connection_msg)
        print(len(self._links))

    async def read_from_connection(self, client_id, reader):
        while 1:
            line = await reader.readline()
            print(line)
            if not line:
                self._remove_client(client_id)
                break
            
    def _remove_client(self, client_id):
        client = self._links.pop(client_id)
        client[0].close()
        client[1].close()
        print(len(self._links))