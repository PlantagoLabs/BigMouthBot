from BMBLib.encoder import Encoder
from BMBLib.motor import Motor
from BMBLib.internals import BatteryMonitor
from BMBLib.control import BasicControl
import time
import uasyncio

motor_models = {'left': [(0.8935633, -0.4466964), (0.9094235, 0.4428077)], 'right': [(0.8396645, -0.313951), (0.8680304, 0.3420231)]}

battery = BatteryMonitor()

l_encoder = Encoder(0, 4, 5, flip_dir=True)
l_motor = Motor(6, 7, flip_dir=True, motor_model=motor_models['left'], voltage_func=battery.get_battery_voltage)

r_encoder = Encoder(1, 12, 13)
r_motor = Motor(14, 15, motor_model=motor_models['right'], voltage_func=battery.get_battery_voltage)

l_controller = BasicControl(l_encoder.get_wheel_speed, l_motor.set_speed)
l_controller.force_command(0)
r_controller = BasicControl(r_encoder.get_wheel_speed, r_motor.set_speed)
r_controller.force_command(0)

async def main():
    await uasyncio.sleep(3)
    
    list_kp = []
    list_scores = []
    
    for k in range(0, 16):
        kp = k/2. 
        l_controller.set_proportional_gain(kp)
        l_controller.set_integrator(0.2*kp, 2)
        
        r_controller.set_proportional_gain(kp)
        r_controller.set_integrator(0.2*kp, 2)
        
        mse = 0
        dt_mse = 0
        
        target = 1
        l_controller.set_target(target)
        r_controller.set_target(target)
        await uasyncio.sleep_ms(600)
        
        l_prev_speed = None
        r_prev_speed = None
        
        for it in range(120):
            l_speed = l_encoder.get_wheel_speed()
            r_speed = l_encoder.get_wheel_speed()
            if l_prev_speed is not None:
                accel = l_speed - l_prev_speed
                dt_mse += accel*accel
            if r_prev_speed is not None:
                accel = r_speed - r_prev_speed
                dt_mse += accel*accel
            l_prev_speed = l_speed
            r_prev_speed = r_speed
            mse += (l_speed - target)*(l_speed - target) + (r_speed - target)*(r_speed - target)
            await uasyncio.sleep_ms(25)
            
        l_controller.force_command(0)
        r_controller.force_command(0)
        await uasyncio.sleep_ms(400)
            
        target = -1
        l_controller.set_target(target)
        r_controller.set_target(target)
        await uasyncio.sleep_ms(600)
        
        l_prev_speed = None
        r_prev_speed = None
        
        for it in range(120):
            l_speed = l_encoder.get_wheel_speed()
            r_speed = l_encoder.get_wheel_speed()
            if l_prev_speed is not None:
                accel = l_speed - l_prev_speed
                dt_mse += accel*accel
            if r_prev_speed is not None:
                accel = r_speed - r_prev_speed
                dt_mse += accel*accel
            l_prev_speed = l_speed
            r_prev_speed = r_speed
            mse += (l_speed - target)*(l_speed - target) + (r_speed - target)*(r_speed - target)
            await uasyncio.sleep_ms(25)
            
        l_controller.force_command(0)
        r_controller.force_command(0)
        await uasyncio.sleep_ms(400)
        
        # print(l_controller.Ipos, l_controller.Ineg)
        # print(r_controller.Ipos, r_controller.Ineg)
        print(kp, mse, dt_mse)
        
        list_kp.append(kp)
        list_scores.append(mse + dt_mse)

        
    min_score = min(list_scores)
    
    sum_kp = 0
    num_kp = 0
    max_kp = 0
    
    for index, score in enumerate(list_scores):
        if score < 3*min_score:
            sum_kp += list_kp[index]
            num_kp += 1
            max_kp = max(max_kp, list_kp[index])
            
    print(sum_kp/num_kp, max_kp, (sum_kp/num_kp + max_kp)/2)

uasyncio.run(main())