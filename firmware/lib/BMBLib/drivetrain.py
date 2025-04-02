from BMBLib.encoder import Encoder
from BMBLib.motor import Motor
from BMBLib.control import BasicControl

from BMBLib import synapse

class Drivetrain():
    def __init__(self, motor_models, voltage_func=None):
        self.wheel_circumference = 50
        self.wheel_distance = 130

        self.l_encoder = Encoder(0, 4, 5, flip_dir=True)
        self.l_motor = Motor(6, 7, flip_dir=True, motor_model=motor_models['motor_models']['left'], voltage_func=voltage_func)
        self.previous_l_encoder_value = 0.0

        self.r_encoder = Encoder(1, 12, 13)
        self.r_motor = Motor(14, 15, motor_model=motor_models['motor_models']['right'],  voltage_func=voltage_func)
        self.previous_r_encoder_value = 0.0

        self.l_controller = BasicControl(self.l_encoder.get_wheel_speed, self.l_motor.set_speed)
        self.l_controller.force_command(0)
        self.l_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
        self.l_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

        self.r_controller = BasicControl(self.r_encoder.get_wheel_speed, self.r_motor.set_speed)
        self.r_controller.force_command(0)
        self.r_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
        self.r_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

    def set_velocity(self, forward_speed, rotation_speed):
        pass

    def get_encoder_data():
        pass

    def _act_stop_message(self, topic, message, source):
        pass

    def _act_velocity_message(self, topic, message, source):
        pass

