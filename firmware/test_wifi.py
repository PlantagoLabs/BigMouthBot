import network
import asyncio
import json
from BMBLib import synapse
from BMBLib.bmbnet import BMBLink
from BMBLib import setup

wlan = network.WLAN()
wlan.active(True)

with open('wifi_logins.json', 'r') as fid:
    known_wifis = json.load(fid)

wifi_points = wlan.scan()
for point in wifi_points:
    point_name = point[0].decode()
    if point_name in known_wifis:
        wlan.connect(point_name, known_wifis[point_name])
        print(f'connecting to {point_name}')
        break

print(wlan.isconnected())
ip = wlan.ifconfig()
print(ip)
print(wlan.status())
# new_ip = ('192.168.221.123', ip[1], ip[2], ip[3])
# print(new_ip)
# wlan.ifconfig(new_ip)
print(wlan.isconnected())
print(wlan.status())

link_manager = BMBLink()
initial_data = {'topic': 'welcome', 
                'source': 'connection',
                'message': "You are connected :)"}
link_manager.on_connection_msg = json.dumps(initial_data) + '\n'


synapse.subscribe("v_batt", link_manager.send_synaptic_mssage)
synapse.subscribe("l_reflect", link_manager.send_synaptic_mssage)
synapse.subscribe("r_reflect", link_manager.send_synaptic_mssage)
synapse.subscribe("range_array", link_manager.send_synaptic_mssage)
synapse.subscribe("cpu_profile", link_manager.send_synaptic_mssage)
synapse.subscribe("memory", link_manager.send_synaptic_mssage)
synapse.subscribe("imu", link_manager.send_synaptic_mssage)
synapse.subscribe("imu", link_manager.send_synaptic_mssage)
synapse.subscribe("estimate.position", link_manager.send_synaptic_mssage)
synapse.subscribe("encoder.speed", link_manager.send_synaptic_mssage)
synapse.subscribe("control", link_manager.send_synaptic_mssage)

async def main_loop():
    while 1:
        print('looping')
        # await link_manager.send_synaptic_mssage("test", "apple", "bmb")
        await asyncio.sleep_ms(1000)
        
server = asyncio.run(asyncio.start_server(link_manager.handle_connection, ip[0], 2132))

asyncio.run(main_loop())


        
    