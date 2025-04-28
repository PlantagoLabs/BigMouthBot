from machine import I2C, Pin

def make_buzz(freq, volume, duration, i2c, addr=52):
    msg = freq.to_bytes(2, 'big') + volume.to_bytes(1, 'big') + duration.to_bytes(2, 'big') + b'\x01'
    i2c.writeto_mem(addr, 3, msg)

i2c = I2C(1, scl=Pin(19), sda= Pin(18), freq=1_000_000)

make_buzz(262, 4, 200, i2c)

import json
import gc
import os
import time

# from BMBLib.encoder import Encoder
# from BMBLib.motor import Motor
# from BMBLib.control import BasicControl

from BMBLib.drivetrain import Drivetrain
from BMBLib.servo import Servo

from BMBLib.internals import BatteryMonitor
from BMBLib import reflectance
from BMBLib.range_array_driver import RangeArrayDriver

from BMBLib.position_estimation import SimplePositionEstimator

from BMBLib import synapse
from BMBLib import profiler

from async_buzzer import AsyncI2CBuzzer, tabs_to_notes, text_to_tunetalk_tabs

from LSM6DSO import LSM6DSO

make_buzz(330, 4, 200, i2c)

battery = BatteryMonitor()

with open('motor_model.json', 'r') as fid:
    motor_models = json.load(fid)

drivetrain = Drivetrain(motor_models, battery.get_battery_voltage)
try:
    imu = LSM6DSO(i2c)
except:
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

try:
    range_array = RangeArrayDriver(i2c)
except:
    make_buzz(131, 4, 1000, i2c)
    time.sleep(1)

make_buzz(349, 4, 200, i2c)
time.sleep_ms(200)
    
buzzer = AsyncI2CBuzzer(i2c)

servo_1 = Servo.get_default_servo(1)

position_estimation = SimplePositionEstimator()

@profiler.profile("memory.status")
def get_memory_status():
    gc.collect() #collect now to have an accurate amount of what is actually in use
    storage_stats = os.statvfs('/')
    memory = {'ram': {'allocated': gc.mem_alloc(), 'free': gc.mem_free()}, 
              'storage': {'allocated': storage_stats[2] - storage_stats[3], 'free': storage_stats[3]}}
    print(memory)
    return memory

@profiler.profile("imu.read")
def get_imu_data():
    global imu
    return imu.get_dict()

@profiler.profile("tunetalk")
def tunetalk(message):
    global buzzer
    return buzzer.replace(tabs_to_notes(text_to_tunetalk_tabs(message), unit_length=150))

synapse.survey("v_batt", battery.get_battery_voltage, 500, "synaptic")
synapse.survey("l_reflect", reflectance.get_left_reflectance, 200, "synaptic")
synapse.survey("r_reflect", reflectance.get_right_reflectance, 200, "synaptic")
synapse.survey("cpu_profile", profiler.get_profiler_data, 1000, "synaptic")
synapse.survey("memory", get_memory_status, 1000, "synaptic")
synapse.survey("imu", get_imu_data, 40, "synaptic")

synapse.apply("mouth.angle", servo_1.set_angle)
synapse.apply("mouth.free", servo_1.free)

synapse.apply("tunetalk", tunetalk)

make_buzz(392, 4, 200, i2c)