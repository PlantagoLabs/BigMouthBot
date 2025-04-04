import json

from machine import I2C, Pin

from BMBLib.encoder import Encoder
from BMBLib.motor import Motor
from BMBLib.control import BasicControl

from BMBLib.internals import BatteryMonitor

from BMBLib import synapse

from BMBLib.servo import Servo

from async_buzzer import AsyncI2CBuzzer

from LSM6DSO import LSM6DSO

i2c = I2C(1, scl=Pin(19), sda= Pin(18), freq=1_000_000)

battery = BatteryMonitor()

with open('motor_model.json', 'r') as fid:
    motor_models = json.load(fid)

l_encoder = Encoder(0, 4, 5, flip_dir=True)
l_motor = Motor(6, 7, flip_dir=True, motor_model=motor_models['motor_models']['left'], voltage_func=battery.get_battery_voltage)

r_encoder = Encoder(1, 12, 13)
r_motor = Motor(14, 15, motor_model=motor_models['motor_models']['right'],  voltage_func=battery.get_battery_voltage)

l_controller = BasicControl(l_encoder.get_wheel_speed, l_motor.set_speed)
l_controller.force_command(0)
l_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
l_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

r_controller = BasicControl(r_encoder.get_wheel_speed, r_motor.set_speed)
r_controller.force_command(0)
r_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
r_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

imu = LSM6DSO(i2c)

buzzer = AsyncI2CBuzzer(i2c)

synapse.survey("v_batt", battery.get_battery_voltage, 1000, "bmb")
synapse.survey("imu", imu.get_dict, 100, "bmb")

servo_1 = Servo.get_default_servo(1)