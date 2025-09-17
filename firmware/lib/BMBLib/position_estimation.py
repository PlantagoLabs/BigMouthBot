import math
import time

from BMBLib import synapse
from BMBLib import profiler

class SimplePositionEstimator:
    def __init__(self, use_imu = True):
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0

        self.previous_forward = 0.0

        self.imu_previous_time_tick = time.ticks_us()
        self.gyro_z_bias = None
        self.gyro_z_buffer = []

        self.use_imu = use_imu

        synapse.apply('encoder.motion', self.update_position_with_encoders)
        synapse.apply('imu', self._do_update_position_with_imu)

    @profiler.profile("estimator.encoders")
    def _do_update_position_with_encoders(self, motion):
        d_forward = motion['forward'] - self.previous_forward

        if not self.use_imu:
            self.heading = motion['heading']

        self.x += d_forward*math.cos(self.heading)
        self.y += d_forward*math.sin(self.heading)

        self.previous_forward = motion['forward']

    @profiler.profile("estimator.imu")
    def _do_update_position_with_imu(self, imu):
        if not self.use_imu:
            return
        new_time_tick = time.ticks_us()
        dtick = time.ticks_diff(new_time_tick, self.imu_previous_time_tick)

        d_heading = imu['gyro'][2]*dtick*1e-6
        self.heading += d_heading
        self.imu_previous_time_tick = new_time_tick

    
    def update_position_with_encoders(self, motion):
        self._do_update_position_with_encoders(motion)

        synapse.publish('estimate.pose', [self.x, self.y, self.heading], 'simple_estimator')



    

