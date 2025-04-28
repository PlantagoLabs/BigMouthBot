import math

from BMBLib import synapse
from BMBLib import profiler

class SimplePositionEstimator:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0

        self.previous_forward = 0.0
        self.previous_heading = 0.0

        synapse.apply('encoder.motion', self.update_position_with_encoders)

    @profiler.profile("estimator.encoders")
    def _do_update_position_with_encoders(self, motion):
        d_forward = motion['forward'] - self.previous_forward
        d_heading = motion['heading'] - self.previous_heading

        self.x += d_forward*math.cos(self.heading + d_heading/2)
        self.y += d_forward*math.sin(self.heading + d_heading/2)

        self.heading += d_heading

        self.previous_forward = motion['forward']
        self.previous_heading = motion['heading']
    
    def update_position_with_encoders(self, motion):
        self._do_update_position_with_encoders(motion)

        synapse.publish('estimate.position', {'x': self.x, 'y': self.y, 'heading': self.heading}, 'simple_estimator')



    

