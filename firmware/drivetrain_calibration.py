from BMBLib.encoder import Encoder
from BMBLib.motor import Motor
from BMBLib.internals import BatteryMonitor
import time
import uasyncio
import json

def add_sample_to_motor_data(motor_data, voltage, speed):
    motor_data[0] += 1
    motor_data[1] += voltage
    motor_data[2] += voltage*voltage
    motor_data[3] += speed
    motor_data[4] += voltage*speed

def compute_motor_model(motor_data):
    det = motor_data[0]*motor_data[2] - motor_data[1]*motor_data[1]
    c1 = (motor_data[0]*motor_data[4] - motor_data[1]*motor_data[3])/det
    k = (motor_data[1]*motor_data[4] - motor_data[2]*motor_data[3])/det
    c2 = k/c1

    return (c1, c2)

async def main():
    battery = BatteryMonitor()
    await uasyncio.sleep(3)
    
    left_forward_motor_data = [0, 0., 0., 0., 0.]
    left_backward_motor_data = [0, 0., 0., 0., 0.]
    right_forward_motor_data = [0, 0., 0., 0., 0.]
    right_backward_motor_data = [0, 0., 0., 0., 0.]
    
    l_encoder = Encoder(0, 4, 5, flip_dir=True)
    l_motor = Motor(6, 7, flip_dir=True, voltage_func=battery.get_battery_voltage)
    
    r_encoder = Encoder(1, 12, 13)
    r_motor = Motor(14, 15, voltage_func=battery.get_battery_voltage)

    for vi in range(0, 44, 2):
        voltage = vi/10.0
        r_motor.set_voltage(voltage)
        l_motor.set_voltage(voltage)
        await uasyncio.sleep_ms(800)
        for it in range(20):
            l_speed = l_encoder.get_wheel_speed()
            r_speed = r_encoder.get_wheel_speed()
            print(l_speed, r_speed)
            if l_speed > 0.6:
                add_sample_to_motor_data(left_forward_motor_data, voltage, l_speed)
            if r_speed > 0.6:
                add_sample_to_motor_data(right_forward_motor_data, voltage, r_speed)
            await uasyncio.sleep_ms(100)
            
        r_motor.set_voltage(-voltage)
        l_motor.set_voltage(-voltage)
        await uasyncio.sleep_ms(800)
        for it in range(20):
            l_speed = l_encoder.get_wheel_speed()
            r_speed = r_encoder.get_wheel_speed()
            print(l_speed, r_speed)
            if l_speed < -0.6:
                add_sample_to_motor_data(left_backward_motor_data, -voltage, l_speed)
            if r_speed < -0.6:
                add_sample_to_motor_data(right_backward_motor_data, -voltage, r_speed)
            await uasyncio.sleep_ms(100)     

    r_motor.set_voltage(0)
    l_motor.set_voltage(0)       

    await uasyncio.sleep(1)

    with open('motor_model.json', 'r') as fid:
        motor_models = json.load(fid)

    print(left_backward_motor_data)
    print(left_forward_motor_data)
    print(right_backward_motor_data)
    print(right_forward_motor_data)

    motor_models['motor_models'] = {'left': [compute_motor_model(left_backward_motor_data), compute_motor_model(left_forward_motor_data)],
                    'right': [compute_motor_model(right_backward_motor_data), compute_motor_model(right_forward_motor_data)]}
    
    print(motor_models)

    with open('motor_model.json', 'w') as fid:
        json.dump(motor_models, fid)

uasyncio.run(main())