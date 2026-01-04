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

# ip = '192.168.135.99'
# ip = '192.168.21.110'
# ip = '192.168.231.99'
ip = '192.168.68.111'
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

ui_grid = UIGrid(bottom_frame, 2, ['range_array', 'log', 'cpu', 'trajectory'])

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

phi = 0

def redraw_plot():
    global incoming_queue
    global outgoing_queue
    global ui_grid

    messages = []
    
    while not incoming_queue.empty():
        messages.append(incoming_queue.get())

    ui_grid.update_blocks_with_messages(messages)

    root.after(30, redraw_plot)

redraw_plot()

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.