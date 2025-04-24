import json

from machine import I2C, Pin
import gc
import os

# from BMBLib.encoder import Encoder
# from BMBLib.motor import Motor
# from BMBLib.control import BasicControl

from BMBLib.drivetrain import Drivetrain
from BMBLib.servo import Servo

from BMBLib.internals import BatteryMonitor
from BMBLib import reflectance
from BMBLib.range_array_driver import RangeArrayDriver

from BMBLib import synapse
from BMBLib import profiler

from async_buzzer import AsyncI2CBuzzer

from LSM6DSO import LSM6DSO

i2c = I2C(1, scl=Pin(19), sda= Pin(18), freq=1_000_000)

battery = BatteryMonitor()

with open('motor_model.json', 'r') as fid:
    motor_models = json.load(fid)

drivetrain = Drivetrain(motor_models, battery.get_battery_voltage)

imu = LSM6DSO(i2c)
range_array = RangeArrayDriver(i2c)

buzzer = AsyncI2CBuzzer(i2c)

servo_1 = Servo.get_default_servo(1)

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

synapse.survey("v_batt", battery.get_battery_voltage, 500, "synaptic")
synapse.survey("l_reflect", reflectance.get_left_reflectance, 200, "synaptic")
synapse.survey("r_reflect", reflectance.get_right_reflectance, 200, "synaptic")
synapse.survey("cpu_profile", profiler.get_profiler_data, 1000, "synaptic")
synapse.survey("memory", get_memory_status, 1000, "synaptic")
synapse.survey("imu", get_imu_data, 100, "synaptic")

synapse.apply("mouth.angle", servo_1.set_angle)
synapse.apply("mouth.free", servo_1.free)