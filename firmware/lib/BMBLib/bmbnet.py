import network
import asyncio
import json
from BMBLib import profiler
from BMBLib import synapse

class BMBLink():
    def __init__(self):
        self.on_connection_msg = None

        self._latest_id = 0
        self._links = {}

    @profiler.profile("bmbnet.send")
    async def send_message(self, message):
        for client_id in self._links:
            try:
                self._links[client_id][1].write(message)
                await self._links[client_id][1].drain()
            except:
                print(f'connection reset from {client_id}')
                self._remove_client(client_id)
                

    def send_synaptic_mssage(self, topic, message, source):
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
            try:
                line = await reader.readline()
            except:
                print(f'connection reset from {client_id}')
                self._remove_client(client_id)
                break

            print(line)
            if not line:
                self._remove_client(client_id)
                break

            try:
                data = json.loads(line.decode())
                if 'topic' not in data or 'message' not in data:
                    continue
                if 'source' not in data:
                    data['source'] = None
            except:
                print(line)
                continue

            synapse.publish(data['topic'], data['message'], data['source'])
                
            
    def _remove_client(self, client_id):
        if client_id in self._links:
            client = self._links.pop(client_id)
            client[0].close()
            client[1].close()
        print(len(self._links))