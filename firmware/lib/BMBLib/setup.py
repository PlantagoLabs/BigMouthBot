import json

from machine import I2C, Pin

# from BMBLib.encoder import Encoder
# from BMBLib.motor import Motor
# from BMBLib.control import BasicControl

from BMBLib.drivetrain import Drivetrain

from BMBLib.internals import BatteryMonitor

from BMBLib import synapse

from BMBLib.servo import Servo

from async_buzzer import AsyncI2CBuzzer

from LSM6DSO import LSM6DSO

i2c = I2C(1, scl=Pin(19), sda= Pin(18), freq=1_000_000)

battery = BatteryMonitor()

with open('motor_model.json', 'r') as fid:
    motor_models = json.load(fid)

drivetrain = Drivetrain(motor_models, battery.get_battery_voltage)

imu = LSM6DSO(i2c)

buzzer = AsyncI2CBuzzer(i2c)

synapse.survey("v_batt", battery.get_battery_voltage, 1000, "internal")
synapse.survey("imu", imu.get_dict, 100, "imu")

servo_1 = Servo.get_default_servo(1)