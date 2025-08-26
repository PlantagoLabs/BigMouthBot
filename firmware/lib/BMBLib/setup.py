from machine import I2C, Pin

i2c = I2C(1, scl=Pin(19), sda= Pin(18), freq=400_000, timeout=200000)

print(i2c.scan())

def make_buzz(freq, volume, duration, i2c, addr=52):
    msg = freq.to_bytes(2, 'big') + volume.to_bytes(1, 'big') + duration.to_bytes(2, 'big') + b'\x01'
    i2c.writeto_mem(addr, 3, msg)

DEFAULT_VOLUME = 4

make_buzz(262, DEFAULT_VOLUME, 200, i2c)

from BMBLib import synapse

def print_logs(topic, message, source):
    print(f'{source}: {message}')

synapse.subscribe('log', print_logs)

import json
import gc
import os
import time
import asyncio

# from BMBLib.encoder import Encoder
# from BMBLib.motor import Motor
# from BMBLib.control import BasicControl

from BMBLib.drivetrain import Drivetrain
from BMBLib.servo import Servo

from BMBLib.internals import BatteryMonitor
from BMBLib import reflectance
from BMBLib.range_array_driver import RangeArrayDriver

from BMBLib.position_estimation import SimplePositionEstimator

from BMBLib import profiler

import async_buzzer
async_buzzer.DEFAULT_VOLUME = DEFAULT_VOLUME
from async_buzzer import AsyncI2CBuzzer, tabs_to_notes, text_to_tunetalk_tabs

from BMBLib.imu import LSM6DSOIMU

from AMG8833 import AMG8833

from APDS9960 import APDS9960LITE

from BMBLib.ultrasound_range import UltrasoundRange

import network
from BMBLib.bmbnet import BMBLink

make_buzz(330, DEFAULT_VOLUME, 200, i2c)

battery = BatteryMonitor()

with open('motor_model.json', 'r') as fid:
    motor_models = json.load(fid)

drivetrain = Drivetrain(motor_models, battery.get_battery_voltage)

try:
    imu = LSM6DSOIMU(i2c, 40)
except:
    print('Issue with the IMU')
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

try:
    range_array = RangeArrayDriver(i2c)
except:
    print('Issue with the range array')
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

try:
    thermo_cam = AMG8833(i2c)
except:
    print('Issue with the thermo cam')
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

try:
    apds9960=APDS9960LITE(i2c)      # Enable sensor
    apds9960.prox.enableSensor()    # Enable Proximit sensing
    apds9960.prox.eProximityGain = 3
    apds9960.prox.eLEDBoost = 0
except:
    print('Issue with the mouth sensor')
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

make_buzz(349, DEFAULT_VOLUME, 200, i2c)
time.sleep_ms(200)
    
buzzer = AsyncI2CBuzzer(i2c, addr=52)

servo_1 = Servo.get_default_servo(1)

ultrasound = UltrasoundRange()

position_estimation = SimplePositionEstimator()

@profiler.profile("memory.status")
def get_memory_status():
    gc.collect() #collect now to have an accurate amount of what is actually in use
    storage_stats = os.statvfs('/') # use a lib like https://github.com/ifurusato/brushless-motor-controller/blob/main/upy/free.py
    memory = {'ram': {'allocated': gc.mem_alloc(), 'free': gc.mem_free()}, 
              'storage': {'allocated': storage_stats[2] - storage_stats[3], 'free': storage_stats[3]}}
    return memory

@profiler.profile("tunetalk")
def tunetalk(message):
    global buzzer
    return buzzer.replace(tabs_to_notes(text_to_tunetalk_tabs(message), unit_length=150))

@profiler.profile("thermo_cam.read")
def get_thermo_cam_data():
    global thermo_cam
    themo_data = thermo_cam.read_grid()
    return themo_data

@profiler.profile("mouth.prox.read")
def get_mouth_prox_data():
    global apds9960
    return apds9960.prox.proximityLevel

synapse.survey("v_batt", battery.get_battery_voltage, 500, "synaptic")
synapse.survey("l_reflect", reflectance.get_left_reflectance, 200, "synaptic")
synapse.survey("r_reflect", reflectance.get_right_reflectance, 200, "synaptic")
synapse.survey("cpu_profile", profiler.get_profiler_data, 1000, "synaptic")
synapse.survey("memory", get_memory_status, 1000, "synaptic")
synapse.survey("thermo_cam", get_thermo_cam_data, 100, "synaptic")
synapse.survey("ultrasound.distance", ultrasound.distance, 50, "synaptic")
synapse.survey("mouth.prox", get_mouth_prox_data, 100, "synaptic")

synapse.apply("mouth.angle", servo_1.set_angle)
synapse.apply("mouth.free", servo_1.free)

synapse.apply("tunetalk", tunetalk)

make_buzz(392, DEFAULT_VOLUME, 200, i2c)

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
synapse.subscribe("estimate.position", link_manager.send_synaptic_mssage)
# synapse.subscribe("encoder.speed", link_manager.send_synaptic_mssage)
# synapse.subscribe("control", link_manager.send_synaptic_mssage)
synapse.subscribe("thermo_cam", link_manager.send_synaptic_mssage)
synapse.subscribe("ultrasound.distance", link_manager.send_synaptic_mssage)
synapse.subscribe("log", link_manager.send_synaptic_mssage)
        
server = asyncio.run(asyncio.start_server(link_manager.handle_connection, ip[0], 2132))

profiler.reset()

make_buzz(440, DEFAULT_VOLUME, 200, i2c)