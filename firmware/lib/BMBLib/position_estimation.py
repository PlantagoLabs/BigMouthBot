import math
import time

from BMBLib import synapse
from BMBLib import profiler

class SimplePositionEstimator:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0

        self.previous_forward = 0.0

        self.imu_previous_time_tick = time.ticks_us()
        self.gyro_z_bias = None
        self.gyro_z_buffer = []

        synapse.apply('encoder.motion', self.update_position_with_encoders)
        synapse.apply('imu', self._do_update_position_with_imu)

    @profiler.profile("estimator.encoders")
    def _do_update_position_with_encoders(self, motion):
        d_forward = motion['forward'] - self.previous_forward

        self.x += d_forward*math.cos(self.heading)
        self.y += d_forward*math.sin(self.heading)

        self.previous_forward = motion['forward']

    @profiler.profile("estimator.imu")
    def _do_update_position_with_imu(self, imu):
        new_time_tick = time.ticks_us()
        dtick = time.ticks_diff(new_time_tick, self.imu_previous_time_tick)
        if self.gyro_z_bias is None:
            if len(self.gyro_z_buffer) < 30:
                self.gyro_z_buffer.append(imu['gyro'][2])
            else:
                self.gyro_z_bias = 0.0
                for val in self.gyro_z_buffer:
                    self.gyro_z_bias += val
                self.gyro_z_bias /= len(self.gyro_z_buffer)
                print(self.gyro_z_bias)
        else:
            d_heading = (imu['gyro'][2] - self.gyro_z_bias)*dtick*1e-6
            self.heading += d_heading
            self.imu_previous_time_tick = new_time_tick

    
    def update_position_with_encoders(self, motion):
        self._do_update_position_with_encoders(motion)

        synapse.publish('estimate.position', {'x': self.x, 'y': self.y, 'heading': self.heading}, 'simple_estimator')



    

