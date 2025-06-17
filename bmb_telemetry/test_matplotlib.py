import tkinter
import sys
import os

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from bmb_link_client import BMBLinkClient
from multiqueue import multiqueue

import numpy as np
import time

from queue import Queue

from graph_plotters import *

from ui_block import UIGrid

from telemind import TeleMind

plt.style.use('dark_background')

app_running = True

ip = '192.168.68.107'
# ip = '192.168.21.110'
# ip = '192.168.231.99'
port = 2132

print('before bmb client')

bmbclient = BMBLinkClient(ip, port, record=True)

# telemind = TeleMind(main_task)

outgoing_queue, incoming_queue = multiqueue.get_queues()

root = tkinter.Tk()
root.wm_title("Embedding in Tk")
root.configure(background='black')

top_frame = tkinter.Frame(root)
top_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
top_frame['bg'] = 'black'
def _quit():
    print('quitting')
    bmbclient.stop()
    print('bmb link shut down')
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    time.sleep(0.5)
    print('exiting')
    os._exit(0)

def connect():
    global connect_entry
    print('connect', connect_entry.get())
    bmbclient = BMBLinkClient(ip, port, record=True)

connect_frame = tkinter.Frame(top_frame)
connect_frame.pack(side=tkinter.LEFT, expand=1)

connect_entry = tkinter.Entry(connect_frame, width=20)
connect_entry.pack(side=tkinter.LEFT, expand=1)

connect_button = tkinter.Button(master=connect_frame, text="Connect", command=connect)
connect_button.pack(side=tkinter.LEFT, expand=1)

quit_button = tkinter.Button(master=top_frame, text="Quit", command=_quit)
quit_button.pack(side=tkinter.LEFT, expand=1)

bottom_frame = tkinter.Frame(root)
bottom_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
bottom_frame['bg'] = 'black'

ui_grid = UIGrid(bottom_frame, 2, ['range_array', 'thermo_cam', 'cpu', 'imu'])

# sensor_frame = tkinter.Frame(root)

# v_batt_timeline = TimelinePlotter(sensor_frame, y_lim=[3.6, 6.0], y_label='Voltage [V]')
# v_batt_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# v_batt_timeline.draw()
# reflect_timeline = TimelinePlotter(sensor_frame, y_lim=[0, 1], y_label='Reflectance [-]')
# reflect_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# reflect_timeline.draw()

# memory_frame = tkinter.Frame(root)

# ram_timeline = StackedLinePlotter(memory_frame, y_label='RAM [kB]')
# ram_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# ram_timeline.draw()
# storage_timeline = StackedLinePlotter(memory_frame, y_label='Storage [Nodes]')
# storage_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# storage_timeline.draw()

# imu_frame = tkinter.Frame(root)
# acc_timeline = TimelinePlotter(imu_frame, max_num_samples = 300, y_label='Acceleration [?]')
# acc_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# acc_timeline.draw()
# gyro_timeline = TimelinePlotter(imu_frame, max_num_samples = 300, y_label='Rotation Speed [?]')
# gyro_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# gyro_timeline.draw()

# encoder_frame = tkinter.Frame(root)
# encoder_timeline = TimelinePlotter(encoder_frame, max_num_samples = 300, y_label='Encoder Speed [?]')
# encoder_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# encoder_timeline.draw()
# control_timeline = TimelinePlotter(encoder_frame, max_num_samples = 300, y_label='Control Values [?]')
# control_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# control_timeline.draw()
# # gyro_timeline = TimelinePlotter(imu_frame, max_num_samples = 300, y_label='Rotation Speed [?]')
# # gyro_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# # gyro_timeline.draw()

# # trajectory_plotter = TrajectoryPlotter(root)
# # trajectory_plotter.get_tk_widget().grid(row=1, column=0) 
# # trajectory_plotter.draw()

# range_array_img = GridPlotter(root, c_lim=[0, 2000])
# range_array_img.get_tk_widget().grid(row=0, column=1)#pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# range_array_img.draw()

# cpu_usage_img = PiePlotter(root)
# cpu_usage_img.get_tk_widget().grid(row=1, column=1)#pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
# cpu_usage_img.draw()

# actuator_frame = tkinter.Frame(root)

# spinval = tkinter.IntVar(value=50)
# def servo_value_changed():
#     print(spinval.get())
#     bmbclient.outgoing_queue.put({'topic': 'mouth.angle', 'message': spinval.get(), 'source': 'telemetry'})
# servo_spinbox = tkinter.Spinbox(actuator_frame, from_=0.0, to=100.0, textvariable=spinval, command=servo_value_changed)
# servo_spinbox.pack(side=tkinter.TOP)

# sensor_frame.grid(row=0, column=0)
# memory_frame.grid(row=1, column=2)
# imu_frame.grid(row=1, column=0) 
# # encoder_frame.grid(row=1, column=0)
# actuator_frame.grid(row=0, column=2)

motion_speeds = {'forward_speed': 0, 'yaw_rate': 0}

def send_motion_message():
    outgoing_queue.put({'topic': 'drivetrain.set_velocity', 
                        'message': motion_speeds, 
                        'source': 'telemetry'})
    
def send_stop_message():
    outgoing_queue.put({'topic': 'drivetrain.stop', 
                        'message': None, 
                        'source': 'telemetry'})

def on_key_press(event):
    global motion_speeds
    print(event.keysym)
    if event.keysym == 'Up':
        motion_speeds['forward_speed'] += 20
    if event.keysym == 'Down':
        motion_speeds['forward_speed'] -= 20
    if event.keysym == 'Left':
        motion_speeds['yaw_rate'] += 0.3
    if event.keysym == 'Right':
        motion_speeds['yaw_rate'] -= 0.3
    if event.keysym == 'space':
        motion_speeds = {'forward_speed': 0, 'yaw_rate': 0}
    send_motion_message()

    # outgoing_queue.put({'topic': 'tunetalk', 
    #                     'message': event.keysym[0], 
    #                     'source': 'telemetry'})

    if event.keysym == 'space':
        send_stop_message()

root.bind("<KeyPress>", on_key_press)


# def _quit():
#     root.quit()     # stops mainloop
#     root.destroy()  # this is necessary on Windows to prevent
#                     # Fatal Python Error: PyEval_RestoreThread: NULL tstate


# button = tkinter.Button(master=root, text="Quit", command=_quit)
# button.pack(side=tkinter.BOTTOM)

phi = 0

def redraw_plot():
    global incoming_queue
    global outgoing_queue
    global ui_grid

    messages = []
    
    while not incoming_queue.empty():
        messages.append(incoming_queue.get())

    ui_grid.update_blocks_with_messages(messages)

    
    #     if data['topic'] == 'v_batt':
    #         v_batt_timeline.add_data(data['message'], data['timestamp'], 'v_batt')
    #     elif 'reflect' in data['topic']:
    #         reflect_timeline.add_data(data['message'], data['timestamp'], data['topic'])
    #     elif data['topic'] == 'range_array':
    #         range_array_img.add_data(data['message'])
    #     elif data['topic'] == 'cpu_profile':
    #         profiles = {}
    #         total_time_usage = 0
    #         for profile_name in data['message']['profiles']:
    #             profile_time = data['message']['profiles'][profile_name]['time']
    #             total_time_usage += profile_time
    #             if profile_time/(data['message']['runtime']+0.01) > 0.03: 
    #                 profiles[profile_name] = profile_time
    #             else:
    #                 profiles.setdefault('other', 0)
    #                 profiles['other'] += profile_time
    #         profiles['idle'] = max(data['message']['runtime'] - total_time_usage, 0.1)
    #         cpu_usage_img.add_data(profiles)
    #     elif data['topic'] == 'memory':
    #         for label in data['message']['ram']:
    #             data['message']['ram'][label] = data['message']['ram'][label]/1e3
    #         ram_timeline.add_data(list(data['message']['ram'].values()), data['timestamp'], list(data['message']['ram'].keys()))
    #         storage_timeline.add_data(list(data['message']['storage'].values()), data['timestamp'], list(data['message']['storage'].keys()))
    #     elif data['topic'] == 'imu':
    #         pass
    #         acc_timeline.add_data(data['message']['acc'][0], data['timestamp'], 'x')
    #         acc_timeline.add_data(data['message']['acc'][1], data['timestamp'], 'y')
    #         acc_timeline.add_data(data['message']['acc'][2], data['timestamp'], 'z')
    #         gyro_timeline.add_data(data['message']['gyro'][0], data['timestamp'], 'x')
    #         gyro_timeline.add_data(data['message']['gyro'][1], data['timestamp'], 'y')
    #         gyro_timeline.add_data(data['message']['gyro'][2], data['timestamp'], 'z')
    #     # elif data['topic'] == 'estimate.position':
    #     #     trajectory_plotter.add_data(data['message'])
    #     # elif data['topic'] == 'encoder.speed':
    #     #     encoder_timeline.add_data(data['message']['left'], data['timestamp'], data['topic']+".left")
    #     #     encoder_timeline.add_data(data['message']['right'], data['timestamp'], data['topic']+".right")
    #     # elif data['topic'] == 'control':
    #     #     print(data)
    #     #     if data['message']['left']['target'] is not None and data['message']['right']['target'] is not None:
    #     #         encoder_timeline.add_data(data['message']['left']['target'], data['timestamp'], data['topic']+".left")
    #     #         encoder_timeline.add_data(data['message']['right']['target'], data['timestamp'], data['topic']+".right")
    #     #     if data['message']['left']['target'] is not None and data['message']['right']['target'] is not None:
    #     #         control_timeline.add_data(data['message']['left']['target'], data['timestamp'], "target.left")
    #     #         control_timeline.add_data(data['message']['right']['target'], data['timestamp'], "target.right")

    #     #     control_timeline.add_data(data['message']['left']['err'], data['timestamp'], "err.left")
    #     #     control_timeline.add_data(data['message']['right']['err'], data['timestamp'], "err.right")
    #     #     control_timeline.add_data(data['message']['left']['Ipos'], data['timestamp'], "Ipos.left")
    #     #     control_timeline.add_data(data['message']['right']['Ipos'], data['timestamp'], "Ipos.right")
                
    #     else:
    #         print(data)

    # t0 = time.time()
    # v_batt_timeline.draw()
    # reflect_timeline.draw()
    # range_array_img.draw()
    # # encoder_timeline.draw()
    # # control_timeline.draw()
    # acc_timeline.draw()
    # gyro_timeline.draw()
    # # trajectory_plotter.draw()
    # cpu_usage_img.draw()
    # ram_timeline.draw()
    # storage_timeline.draw()
    # print('elapsed', time.time() - t0)

    root.after(30, redraw_plot)

redraw_plot()

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.