import tkinter
from abc import ABC, abstractmethod

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import numpy as np
import threading
from queue import Queue
import asyncio
import json
import time

from graph_plotters import *

plt.style.use('dark_background')

app_running = True

ip = '192.168.68.111'
port = 2132

class ThreadedBMBClient:
    def __init__(self, ip, port):
        self.running = False
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.ip = ip
        self.port = port
        self.connection = threading.Thread(target=self._run_connection).start()

    def _run_connection(self):
        asyncio.run(self.connect())

    async def connect(self):
        self.running = True
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        self.receiver_task = asyncio.create_task(self._receive_data())
        self.send_task = asyncio.create_task(self._send_data())
        while self.running:
            await asyncio.sleep(0.01)
        self.receiver_task.cancel()
        self.send_task.cancel()

    async def _receive_data(self):
        while self.running:
            line = await self.reader.readline()
            try:
                data = json.loads(line)
                data['timestamp'] = time.time()
                self.incoming_queue.put(data)
            except:
                print(line)

    async def _send_data(self):
        while self.running:
            while not self.outgoing_queue.empty():
                message = self.outgoing_queue.get()
                json_msg = (json.dumps(message)+'\n').encode()
                self.writer.write(json_msg)
                await self.writer.drain()
            await asyncio.sleep(0.01)

bmbclient = ThreadedBMBClient(ip, port)

# async def run_tcp_client(msg_queue):
#     global app_running
#     print('connecting to bmb')
#     reader, writer = await asyncio.open_connection(
#         '192.168.68.111', 2132)
    
#     print('connected to bmb')
#     while app_running:
#         line = await reader.readline()
#         try:
#             data = json.loads(line)
#             data['timestamp'] = time.time()
#             msg_queue.put(data)
#         except:
#             print(line)
        
    
# def connect_to_bmb(msg_queue):
#     asyncio.run(run_tcp_client(msg_queue))

# msg_queue = Queue()

# bmb_connection_thread = threading.Thread(target=connect_to_bmb, args=(msg_queue,)).start()

root = tkinter.Tk()
root.wm_title("Embedding in Tk")
root.configure(background='black')

sensor_frame = tkinter.Frame(root)

v_batt_timeline = TimelinePlotter(sensor_frame, y_lim=[3.6, 6.0], y_label='Voltage [V]')
v_batt_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
v_batt_timeline.draw()
reflect_timeline = TimelinePlotter(sensor_frame, y_lim=[0, 1], y_label='Reflectance [-]')
reflect_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
reflect_timeline.draw()

memory_frame = tkinter.Frame(root)

ram_timeline = StackedLinePlotter(memory_frame, y_label='RAM [kB]')
ram_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
ram_timeline.draw()
storage_timeline = StackedLinePlotter(memory_frame, y_label='Storage [Nodes]')
storage_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
storage_timeline.draw()

imu_frame = tkinter.Frame(root)
acc_timeline = TimelinePlotter(imu_frame, y_label='Acceleration [?]')
acc_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
acc_timeline.draw()
gyro_timeline = TimelinePlotter(imu_frame, y_label='Rotation Speed [?]')
gyro_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
gyro_timeline.draw()

range_array_img = GridPlotter(root, c_lim=[0, 500])
range_array_img.get_tk_widget().grid(row=0, column=1)#pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
range_array_img.draw()

cpu_usage_img = PiePlotter(root)
cpu_usage_img.get_tk_widget().grid(row=1, column=1)#pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
cpu_usage_img.draw()

actuator_frame = tkinter.Frame(root)

spinval = tkinter.IntVar(value=50)
def servo_value_changed():
    print(spinval.get())
    bmbclient.outgoing_queue.put({'topic': 'mouth.angle', 'message': spinval.get(), 'source': 'telemetry'})
servo_spinbox = tkinter.Spinbox(actuator_frame, from_=0.0, to=100.0, textvariable=spinval, command=servo_value_changed)
servo_spinbox.pack(side=tkinter.TOP)

sensor_frame.grid(row=0, column=0)
memory_frame.grid(row=1, column=2)
imu_frame.grid(row=1, column=0) 
actuator_frame.grid(row=0, column=2)

# def on_key_press(event):
#     global phi
#     print("you pressed {}".format(event.key))
#     key_press_handler(event, canvas, toolbar)
#     phi += 0.1
#     t = np.arange(0, 3, .01)
#     subplt.cla()
#     subplt.plot(t, 2 * np.sin(2 * np.pi * t + phi))
#     canvas.draw()

# canvas.mpl_connect("key_press_event", on_key_press)


# def _quit():
#     root.quit()     # stops mainloop
#     root.destroy()  # this is necessary on Windows to prevent
#                     # Fatal Python Error: PyEval_RestoreThread: NULL tstate


# button = tkinter.Button(master=root, text="Quit", command=_quit)
# button.pack(side=tkinter.BOTTOM)

phi = 0

def redraw_plot():
    global bmbclient
    
    while not bmbclient.incoming_queue.empty():
        data = bmbclient.incoming_queue.get()
        if data['topic'] == 'v_batt':
            v_batt_timeline.add_data(data['message'], data['timestamp'], 'v_batt')
        elif 'reflect' in data['topic']:
            reflect_timeline.add_data(data['message'], data['timestamp'], data['topic'])
        elif data['topic'] == 'range_array':
            range_array_img.add_data(data['message'])
        elif data['topic'] == 'cpu_profile':
            profiles = {}
            total_time_usage = 0
            for profile_name in data['message']['profiles']:
                profile_time = data['message']['profiles'][profile_name]['time']
                total_time_usage += profile_time
                if profile_time/(data['message']['runtime']+0.01) > 0.03: 
                    profiles[profile_name] = profile_time
                else:
                    profiles.setdefault('other', 0)
                    profiles['other'] += profile_time
            profiles['idle'] = max(data['message']['runtime'] - total_time_usage, 0.1)
            cpu_usage_img.add_data(profiles)
        elif data['topic'] == 'memory':
            for label in data['message']['ram']:
                data['message']['ram'][label] = data['message']['ram'][label]/1e3
            ram_timeline.add_data(list(data['message']['ram'].values()), data['timestamp'], list(data['message']['ram'].keys()))
            storage_timeline.add_data(list(data['message']['storage'].values()), data['timestamp'], list(data['message']['storage'].keys()))
        elif data['topic'] == 'imu':
            acc_timeline.add_data(data['message']['acc'][0], data['timestamp'], 'x')
            acc_timeline.add_data(data['message']['acc'][1], data['timestamp'], 'y')
            acc_timeline.add_data(data['message']['acc'][2], data['timestamp'], 'z')
            gyro_timeline.add_data(data['message']['gyro'][0], data['timestamp'], 'x')
            gyro_timeline.add_data(data['message']['gyro'][1], data['timestamp'], 'y')
            gyro_timeline.add_data(data['message']['gyro'][2], data['timestamp'], 'z')
        else:
            print(data)

    t0 = time.time()
    v_batt_timeline.draw()
    reflect_timeline.draw()
    range_array_img.draw()
    acc_timeline.draw()
    gyro_timeline.draw()
    cpu_usage_img.draw()
    ram_timeline.draw()
    storage_timeline.draw()
    print('elapsed', time.time() - t0)

    root.after(30, redraw_plot)

redraw_plot()

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.