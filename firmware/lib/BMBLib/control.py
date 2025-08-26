from machine import Timer
from BMBLib import ulinalg
import math

class PIDTimerControl:
    def __init__(self, measure_func, command_func, freq:int=50):
        self.Kp = None
        self.Ki = None
        self.Ilimit = None
        self.Kd = None
        
        self.measure_func = measure_func
        self.command_func = command_func
        self.freq = freq
        
        self.updateTimer = Timer()
        self.updateTimer.init(freq=freq, callback=lambda t:self._update())
        
        self.target = None
        self.command = None

        self.Ipos = 0
        self.Ineg = 0
        self.prev_error = 0
        
    def set_target(self, target):
        self.target = target
        self.command = None

    def force_command(self, command):
        self.command = command

    def set_proportional_gain(self, Kp):
        self.Kp = Kp
        
    def set_integrator_gain(self, Ki, Ilimit):
        self.Ki = Ki
        self.Ilimit = Ilimit
        self.Ipos = 0
        self.Ineg = 0
        
    def _add_error_to_integrator(self, integrator, err):
        integrator += err
        
        if integrator > self.Ilimit:
            integrator = self.Ilimit
        elif integrator < -self.Ilimit:
            integrator = -self.Ilimit
            
        return integrator
        
    def _update(self):
        if self.command is not None:
            self.command_func(self.command)
            return

        if self.target is None:
            return
        
        err = self.target - self.measure_func()
        
        feedback = 0

        if self.Kp:
            feedback += self.Kp*err
            
        if self.Ki:
            if self.target >= 0:
                self.Ipos = self._add_error_to_integrator(self.Ipos, err)
                feedback += self.Ki*self.Ipos
            else:
                self.Ineg = self._add_error_to_integrator(self.Ineg, err)
                feedback += self.Ki*self.Ineg

        # if self.target >= 0 and self.target + feedback < 0:
        #     feedback = -self.target
        # if self.target <= 0 and self.target + feedback > 0:
        #     feedback = -self.target
                     
        self.command_func(self.target + feedback, self.target > 0.0)

        self.prev_error = err
        
class GoToPointControl:
    def __init__(self, speed_gain, speed_range, angle_gain, angle_max_speed):
        
        self.speed_gain = speed_gain
        self.speed_range = speed_range
        self.angle_gain = angle_gain
        self.angle_max_speed = angle_max_speed
    
    def start(self, start_state, target):
        self.target = target
        self.initial_goal_vector = ulinalg.diff_vector(self.target, [start_state['x'], start_state['y']])

    def update(self, current_state):
        current_position = [current_state['x'], current_state['y']]
        vector_to_goal = ulinalg.diff_vector(self.target, current_position)
        if ulinalg.dot(vector_to_goal, self.initial_goal_vector) < 0:
            return None

        goal_heading = ulinalg.heading(vector_to_goal)
        diff_heading = goal_heading - current_state['heading']
        while diff_heading > math.pi:
            diff_heading -= 2*math.pi
        while diff_heading < -math.pi:
            diff_heading += 2*math.pi

        angle_speed_factor = max(math.cos(diff_heading), 0)
        target_speed = angle_speed_factor*min(self.speed_gain*ulinalg.norm(vector_to_goal) + self.speed_range[0], self.speed_range[1])
        angle_speed = self.angle_gain*diff_heading
        if angle_speed > self.angle_max_speed:
            angle_speed = self.angle_max_speed
        elif angle_speed < -self.angle_max_speed:
            angle_speed = -self.angle_max_speed

        return {'forward_speed': target_speed, 'yaw_rate': angle_speed}

