from BMBLib.encoder import Encoder
from BMBLib.motor import Motor
from BMBLib.control import BasicControl

from BMBLib import synapse

class Drivetrain():
    def __init__(self, motor_models, voltage_func=None):
        self.wheel_circumference = 2*3.1415*30
        self.wheel_distance = 154

        self.l_encoder = Encoder(0, 4, 5, flip_dir=True)
        self.l_motor = Motor(6, 7, flip_dir=True, motor_model=motor_models['motor_models']['left'], voltage_func=voltage_func)

        self.r_encoder = Encoder(1, 12, 13)
        self.r_motor = Motor(14, 15, motor_model=motor_models['motor_models']['right'],  voltage_func=voltage_func)

        self.l_controller = BasicControl(self.l_encoder.get_wheel_speed, self.l_motor.set_speed)
        self.l_controller.force_command(0)
        self.l_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
        self.l_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

        self.r_controller = BasicControl(self.r_encoder.get_wheel_speed, self.r_motor.set_speed)
        self.r_controller.force_command(0)
        self.r_controller.set_proportional_gain(motor_models['control_gains']['Kp'])
        self.r_controller.set_integrator_gain(motor_models['control_gains']['Ki'], 12.)

        synapse.subscribe('drivetrain.stop', self._act_stop_message)
        synapse.subscribe('drivetrain.set_velocity', self._act_velocity_message)
        synapse.survey("encoder.motion", self.get_motion_data, 100, "drivetrain")
        synapse.survey("encoder.speed", self.get_encoder_speeds, 100, "drivetrain")
        synapse.survey("control", self.get_control_data, 100, "drivetrain")

    def set_velocity(self, forward_speed, yaw_rate):
        w_r = (forward_speed + 0.5*yaw_rate*self.wheel_distance)/self.wheel_circumference
        w_l = (forward_speed - 0.5*yaw_rate*self.wheel_distance)/self.wheel_circumference

        self.r_controller.set_target(w_r)
        self.l_controller.set_target(w_l)

    def stop(self):
        self.r_controller.force_command(0)
        self.l_controller.force_command(0)

    def get_motion_data(self):
        l_encoder = self.l_encoder.get_wheel_position()
        r_encoder = self.r_encoder.get_wheel_position()
        encoder_data = {'forward': self.wheel_circumference*(l_encoder + r_encoder)/2,
                        'heading': self.wheel_circumference*(r_encoder - l_encoder)/self.wheel_distance}
        return encoder_data
    
    def get_encoder_speeds(self):
        encoder_data = {'left': self.l_encoder.get_wheel_speed(), 'right': self.r_encoder.get_wheel_speed()}
        return encoder_data
    
    def get_control_data(self):
        control_data = {'left': {'err': self.l_controller.prev_error, 
                                 'Ipos': self.l_controller.Ipos, 
                                 'Ineg': self.l_controller.Ineg,
                                 'target': self.l_controller.target}, 
                        'right': {'err': self.r_controller.prev_error, 
                                  'Ipos': self.r_controller.Ipos, 
                                  'Ineg': self.r_controller.Ineg,
                                 'target': self.r_controller.target}}
        return control_data

    def _act_stop_message(self, topic, message, source):
        self.stop()

    def _act_velocity_message(self, topic, message, source):
        self.set_velocity(message['forward_speed'], message['yaw_rate'])

