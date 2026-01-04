from BMBLib import synapse
from BMBLib import ulinalg
import asyncio
import math
import time
from BMBLib.config import config
from BMBLib import profiler

class DifferentialDriveFieldNavigator:
    def __init__(self, period_ms, speed_gain, angle_gain, angle_max_speed, half_fov = math.pi/2):
        self.fields = None
        self.period_ms = period_ms
        synapse.apply('navigator.fields', self.set_new_fields)
        synapse.apply('navigator.deactivate', self.deactivate)
        self.navigate_task = asyncio.create_task(self._navigate_coro())
        self.speed_gain = speed_gain
        self.angle_gain = angle_gain
        self.angle_max_speed = angle_max_speed
        self.half_fov = half_fov

    def set_new_fields(self, new_fields):
        self.fields = new_fields

    def deactivate(self):
        self.fields = None
        synapse.publish('drivetrain.stop', None, 'field_navigator')

    @profiler.profile("navigator.fields")
    def _navigate(self):
        if self.fields is None:
            return
        
        total_vector = [0, 0, 0] # v_x, v_y, yaw rate
        total_weight = 0.0
        total_speed = 0.0
        for field in self.fields:
            field_vector, field_weight = field.get_value()
            if len(field_vector) == 2: # yaw rate is optional
                field_vector += [0]
            weighted_vector = ulinalg.scale_vector(field_vector, field_weight)
            total_vector = ulinalg.add_vector(total_vector, weighted_vector)
            total_weight += field_weight
            total_speed += ulinalg.norm(weighted_vector)

        if total_speed > 1e-6:
            total_vector = ulinalg.scale_vector(total_vector, total_speed/(total_weight*ulinalg.norm(total_vector)) )
        else:
            total_vector = [0, 0, 0]

        speed = self.speed_gain*ulinalg.norm(total_vector[:2])
        
        if speed < 1e-6 and math.abs(total_vector[:2]) < 1e-6:
            synapse.publish('drivetrain.set_velocity', {'forward_speed': 0, 'yaw_rate': 0}, 'navigation_field')
            return

        goal_heading = ulinalg.heading(total_vector)
        diff_heading = goal_heading - synapse.recall_message('estimate.pose')[2]

        diff_heading = ulinalg.wrap_angle(diff_heading)

        scaled_angle = diff_heading*math.pi/(2*self.half_fov)

        scaled_angle = ulinalg.bound_value(scaled_angle, -math.pi/2, math.pi/2)

        angle_speed_factor = max(math.cos(scaled_angle), 0)

        target_speed = angle_speed_factor*speed
        angle_speed = self.angle_gain*diff_heading + total_vector[2]

        angle_speed = ulinalg.bound_value(angle_speed, -self.angle_max_speed, self.angle_max_speed)

        synapse.publish('drivetrain.set_velocity', {'forward_speed': target_speed, 
                                                    'yaw_rate': angle_speed}, 'field_navigator')

        return

    async def _navigate_coro(self):
        while 1:
            self._navigate()
            await asyncio.sleep_ms(self.period_ms)

class SplineFollowingField:
    def __init__(self, trajectory):
        self.trajectory = trajectory
        self.traj_config = config['navigation']['trajectory']

    def get_value(self):
        target = self.trajectory.get_states(time.ticks_ms())
        pose = synapse.recall_message('estimate.pose')
    
        d = ulinalg.diff_vector([target[:2]], [pose[:2]])

        v_s = [target[3], target[4]]
        v_p = [-target[4], target[3]]
        norm_v = ulinalg.norm(v_s)
        if norm_v < 1e-9:
            return [0, 0, 0], 0

        e_l = ulinalg.dot(d, v_p)/norm_v # lateral error
        v_e_l = ulinalg.scale_vector( v_p, self.traj_config['lateral_error_max_speed']*math.atan(self.traj_config['lateral_error_gain']*e_l)/norm_v )

        e_f = ulinalg.dot(d, v_s)/norm_v # forward error
        v_s = ulinalg.scale_vector(v_s, 1 + self.traj_config['forward_error_max_speed']*math.atan(self.traj_config['forward_error_gain']*e_f)/norm_v )
        v_s = ulinalg.add_vector(v_s, v_e_l)

        d_heading = target[2] - pose[2]
        d_heading = ulinalg.wrap_angle(d_heading)

        yaw_rate_c = target[5] + self.traj_config['heading_error_gain']*d_heading

        return v_s.append(yaw_rate_c), self.traj_config['priority']

class GoToPointField:
    def __init__(self, target_point, target_radius, field_priority):
        self.target_point = target_point
        self.target_radius = target_radius
        self.field_priority = field_priority

    def get_value(self):
        vector_to_goal = ulinalg.diff_vector(self.target_point, synapse.recall_message('estimate.pose')[:2])
        distance_to_goal = ulinalg.norm(vector_to_goal)
        if distance_to_goal > self.target_radius:
            return ulinalg.scale_vector(vector_to_goal, 1.0/distance_to_goal), self.field_priority
        else:
            return ulinalg.scale_vector(vector_to_goal, 1.0/self.target_radius), self.field_priority
        
class YeetField:
    def __init__(self, field_priority):
        self.field_priority = field_priority
        self.yeet_urge = 0

    def get_value(self):
        heading = synapse.recall_message('estimate.pose')[2]
        yeet_vector = [math.cos(heading), math.sin(heading)]

        self.yeet_urge += 0.1

        return yeet_vector, 0.5*(1+math.sin(self.yeet_urge))*self.field_priority
    
class InertiaField:
    def __init__(self, field_priority):
        self.field_priority = field_priority
        self.yeet_urge = 0

    def get_value(self):
        heading = synapse.recall_message('estimate.pose')[2]
        forward_vector = [math.cos(heading), math.sin(heading)]

        return forward_vector, self.field_priority

class ObstaclesField:
    def __init__(self, obstacles_topic, active_range, safety_margin, field_priority, repulsive = True):
        self.obstacles_topic = obstacles_topic
        self.active_range = active_range
        self.safety_margin = safety_margin
        self.field_priority = field_priority
        self.repulsive = repulsive

    def get_value(self):

        total_velocity = [0.0, 0.0]
        total_weight = 0.0
        max_weight = 0.0

        robot_position = synapse.recall_message('estimate.pose')[:2]
        
        for obstacle in synapse.recall_message(self.obstacles_topic):
            distance_vect = ulinalg.diff_vector(obstacle, robot_position)
            distance = ulinalg.norm(distance_vect)
            if distance < 1e-6:
                distance = 1e-6
            weight = (self.active_range[1] - (distance - self.safety_margin))/(self.active_range[1]  - self.active_range[0])
            weight = ulinalg.bound_value(weight, 0, 1)
            total_weight += weight
            direction = 1
            if self.repulsive:
                direction = -1
            total_velocity = ulinalg.add_vector(total_velocity, ulinalg.scale_vector(distance_vect, weight*direction/distance))
            max_weight = max(max_weight, weight)

        if total_weight > 1e-6:
            total_velocity = ulinalg.scale_vector(total_velocity, 1/total_weight)
        else:
            total_velocity = [0, 0]

        return total_velocity, self.field_priority*max_weight

class FollowDirectionField:
    def __init__(self, direction_topic, field_priority):
        pass

    def get_value(self):
        pass
    