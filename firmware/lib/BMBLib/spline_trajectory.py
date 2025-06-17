import math
from BMBLib import ulinalg
import time

class CompoundTrajectory:
    def __init__(self, inward_point_scale = 0.0 ,extra_leap_distance = 0.01):
        self.extra_leap_distance = extra_leap_distance
        self.inward_point_scale = inward_point_scale

    def build_trajectory(self, points, initial_speed, start_ticks_ms, cruise_speed, final_speed):
        self.points = []
        self.start_ticks_ms = start_ticks_ms
        self.cruise_speed = cruise_speed
        self.subtrajectories = []

        if len(points) < 2:
            raise ValueError('Not enough points.')
        if len(points) == 2:
            raise ValueError('Not enough points.')

        initial_vect = ulinalg.diff_vector(points[1], points[0])
        travel_dist = ulinalg.norm(initial_vect)
        initial_vel = ulinalg.scale_vector(initial_vect, initial_speed/travel_dist)

        next_leap_vect = ulinalg.diff_vector(points[2], points[0])
        next_vel = ulinalg.scale_vector(next_leap_vect, cruise_speed/(ulinalg.norm(next_leap_vect) + self.extra_leap_distance ))
        

        u_c = ulinalg.add_vector(ulinalg.diff_vector(points[0], points[1]), ulinalg.scale_vector(next_leap_vect, 0.5))
        next_acc = ulinalg.scale_vector(u_c, 4*cruise_speed*cruise_speed/(ulinalg.norm(next_leap_vect)*travel_dist ) )

        inward_offset = ulinalg.scale_vector(u_c, self.inward_point_scale)

        next_point = ulinalg.add_vector(points[1], inward_offset )

        speed_diff_time_factor = max(0.5, 1 + 0.5*(cruise_speed - initial_speed)/cruise_speed)
        
        spline_start_ticks_ms = start_ticks_ms
        total_time_interval = speed_diff_time_factor*(travel_dist - 2*ulinalg.norm(inward_offset))/cruise_speed

        self.subtrajectories.append(PenticSplineTrajectory(points[0], initial_vel, [0, 0], next_point, next_vel, next_acc, 
                                                           start_ticks_ms, total_time_interval))

        self.points.append(points[0])

        for ki in range(1, len(points)-2):
            current_point = next_point
            current_vel = next_vel
            current_acc = next_acc
            next_leap_vect = ulinalg.diff_vector(points[ki+2], points[ki])
            next_vel = ulinalg.scale_vector(next_leap_vect, cruise_speed/(ulinalg.norm(next_leap_vect) + self.extra_leap_distance ))
            travel_dist = ulinalg.norm(ulinalg.diff_vector(points[ki+1], points[ki]))

            u_c = ulinalg.add_vector(ulinalg.diff_vector(points[ki], points[ki+1]), ulinalg.scale_vector(next_leap_vect, 0.5))
            next_acc = ulinalg.scale_vector(u_c, 4*cruise_speed*cruise_speed/(ulinalg.norm(next_leap_vect)*travel_dist ) )

            inward_offset = ulinalg.scale_vector(u_c, self.inward_point_scale)

            next_point = ulinalg.add_vector(points[ki+1], inward_offset )

            spline_start_ticks_ms = time.ticks_add(spline_start_ticks_ms, round(total_time_interval*1000))
            total_time_interval = (1.3 - 0.3*ulinalg.cosine(current_vel, next_vel))*(travel_dist - 2*ulinalg.norm(inward_offset))/cruise_speed

            self.subtrajectories.append(PenticSplineTrajectory(current_point, current_vel, current_acc, next_point, next_vel, next_acc, 
                                                               spline_start_ticks_ms, total_time_interval))

        final_vect = ulinalg.diff_vector(points[-1], points[-2])
        travel_dist = ulinalg.norm(final_vect)
        speed_diff_time_factor = max(0.5, 1 + 0.5*(cruise_speed - final_speed)/cruise_speed)
        spline_start_ticks_ms = time.ticks_add(spline_start_ticks_ms, round(total_time_interval*1000))
        total_time_interval = speed_diff_time_factor*travel_dist/cruise_speed
        final_vel = ulinalg.scale_vector(final_vect, final_speed/travel_dist)

        self.subtrajectories.append(PenticSplineTrajectory(next_point, next_vel, current_acc, points[-1], final_vel, [0, 0], 
                                                           spline_start_ticks_ms, total_time_interval))
        self.points.append(points[-1])

    def get_position(self, ticks_ms):
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)
        if time_diff < 0:
            return self.points[0]
        
        for sub in self.subtrajectories:
            if sub.is_ticks_ms_in_range(ticks_ms):
                return sub.get_position(ticks_ms)
            
        return self.points[-1]
    
    def get_states(self, ticks_ms):
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)
        if time_diff < 0:
            return self.subtrajectories[0].get_states(ticks_ms)
        
        for sub in self.subtrajectories:
            if sub.is_ticks_ms_in_range(ticks_ms):
                return sub.get_states(ticks_ms)
            
        return self.subtrajectories[-1].get_states(ticks_ms)

    def _distance_between_points(self, p1, p2):
        return ulinalg.norm(ulinalg.diff_vector(p1, p2))


class CubicSplineTrajectory:
    def __init__(self, p_start, v_start, p_end, v_end, start_ticks_ms, time_interval):
        self.build_spline(p_start, v_start, p_end, v_end, start_ticks_ms, time_interval)

    def get_states(self, ticks_ms):
        states = []
        velocity = self.get_velocity(ticks_ms)
        states.extend(self.get_position(ticks_ms))
        states.append(self.get_heading(ticks_ms, velocity))
        states.extend(velocity)
        states.append(self.get_rotation_speed(ticks_ms, velocity))
        states.extend(self.get_acceleration(ticks_ms))
        return states

    def get_position(self, ticks_ms):
        t = self._map_time(ticks_ms)
        position = []
        for ki in range(2):
            position.append(self.coefs[ki][0] + self.coefs[ki][1]*t + self.coefs[ki][2]*t**2 + self.coefs[ki][3]*t**3)
        return position
    
    def get_heading(self, ticks_ms, velocity = None):
        if velocity is None:
            velocity = self.get_velocity(ticks_ms)
        if abs(velocity[0]) + abs(velocity[1]) < 1e-12:
            return 0.0
        return math.atan2(velocity[1], velocity[0])

    def get_velocity(self, ticks_ms):
        t = self._map_time(ticks_ms)
        velocity = []
        for ki in range(2):
            velocity.append( (self.coefs[ki][1] + 2*self.coefs[ki][2]*t + 3*self.coefs[ki][3]*t**2)/self.time_interval )
        return velocity
    
    def get_rotation_speed(self, ticks_ms, velocity = None):
        if velocity is None:
            velocity = self.get_velocity(ticks_ms)
        if abs(velocity[0]) + abs(velocity[1]) < 1e-2:
            return 0.0
        accel = self.get_acceleration(ticks_ms)
        return (velocity[0]*accel[1] - velocity[1]*accel[0])/(velocity[0]**2 + velocity[1]**2)
    
    def get_acceleration(self, ticks_ms):
        t = self._map_time(ticks_ms)
        velocity = []
        for ki in range(2):
            velocity.append( (2*self.coefs[ki][2] + 6*self.coefs[ki][3]*t)/(self.time_interval**2) )
        return velocity

    def _map_time(self, ticks_ms):
        if self.time_interval <= 1e-12:
            return 0.0
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)/1000.0
        if time_diff > self.time_interval:
            return 1.0
        if time_diff <= 1e-3:
            return 0.0
        return time_diff/self.time_interval
        
    def is_ticks_ms_in_range(self, ticks_ms):
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)/1000.0
        return (time_diff >= 0) and (time_diff < self.time_interval)

    def build_spline(self, p_start, v_start, p_end, v_end, start_ticks_ms, time_interval):
        self.start_ticks_ms = start_ticks_ms
        self.time_interval = time_interval
        self.coefs = []
        for ki in range(2):
            self.coefs.append([p_start[ki], 
                               v_start[ki]*self.time_interval,
                               3*p_end[ki] - 3*p_start[ki] - 2*v_start[ki]*self.time_interval - v_end[ki]*self.time_interval,
                               v_end[ki]*self.time_interval + v_start[ki]*self.time_interval + 2*p_start[ki] - 2*p_end[ki]])
            
class PenticSplineTrajectory:
    def __init__(self, p_start, v_start, a_start, p_end, v_end, a_end, start_ticks_ms, time_interval):
        self.build_spline(p_start, v_start, a_start, p_end, v_end, a_end, start_ticks_ms, time_interval)
        self._pos_coefs = [1, 1, 1, 1, 1, 1]
        self._vel_coefs = [1, 2, 3, 4, 5]
        self._acc_coefs = [2, 6, 12, 20]

    def get_states(self, ticks_ms):
        states = []
        velocity = self.get_velocity(ticks_ms)
        states.extend(self.get_position(ticks_ms))
        states.append(self.get_heading(ticks_ms, velocity))
        states.extend(velocity)
        states.append(self.get_rotation_speed(ticks_ms, velocity))
        states.extend(self.get_acceleration(ticks_ms))
        return states

    def get_position(self, ticks_ms):
        t = self._map_time(ticks_ms)
        position = []
        for ki in range(2):
            s = 0
            t_power = 1
            for deg in range(6):
                s += self._pos_coefs[deg]*self.coefs[ki][deg]*t_power
                t_power *= t
            position.append(s)
        return position
    
    def get_heading(self, ticks_ms, velocity = None):
        if velocity is None:
            velocity = self.get_velocity(ticks_ms)
        if abs(velocity[0]) + abs(velocity[1]) < 1e-12:
            return 0.0
        return math.atan2(velocity[1], velocity[0])

    def get_velocity(self, ticks_ms):
        t = self._map_time(ticks_ms)
        velocity = []
        for ki in range(2):
            s = 0
            t_power = 1
            for deg in range(5):
                s += self._vel_coefs[deg]*self.coefs[ki][deg+1]*t_power
                t_power *= t
            velocity.append(s/self.time_interval)
        return velocity
    
    def get_rotation_speed(self, ticks_ms, velocity = None):
        if velocity is None:
            velocity = self.get_velocity(ticks_ms)
        if abs(velocity[0]) + abs(velocity[1]) < 1e-2:
            return 0.0
        accel = self.get_acceleration(ticks_ms)
        return (velocity[0]*accel[1] - velocity[1]*accel[0])/(velocity[0]**2 + velocity[1]**2)
    
    def get_acceleration(self, ticks_ms):
        t = self._map_time(ticks_ms)
        acceleration = []
        for ki in range(2):
            s = 0
            t_power = 1
            for deg in range(4):
                s += self._acc_coefs[deg]*self.coefs[ki][deg+2]*t_power
                t_power *= t
            acceleration.append(s/(self.time_interval)**2)
        return acceleration

    def _map_time(self, ticks_ms):
        if self.time_interval <= 1e-12:
            return 0.0
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)/1000.0
        if time_diff > self.time_interval:
            return 1.0
        if time_diff <= 1e-3:
            return 0.0
        return time_diff/self.time_interval
        
    def is_ticks_ms_in_range(self, ticks_ms):
        time_diff = time.ticks_diff(ticks_ms, self.start_ticks_ms)/1000.0
        return (time_diff >= 0) and (time_diff < self.time_interval)


    def build_spline(self, p_start, v_start, a_start, p_end, v_end, a_end, start_ticks_ms, time_interval):
        self.start_ticks_ms = start_ticks_ms
        self.time_interval = time_interval
        ti = self.time_interval
        ti2 = ti*ti
        self.coefs = []
        for ki in range(2):
            self.coefs.append([p_start[ki], 
                               v_start[ki]*ti,
                               0.5*a_start[ki]*ti2,
                               -10*p_start[ki]-6*v_start[ki]*ti-1.5*a_start[ki]*ti2+10*p_end[ki]-4*v_end[ki]*ti +0.5*a_end[ki]*ti2,
                               15*p_start[ki]+8*v_start[ki]*ti+1.5*a_start[ki]*ti2-15*p_end[ki] +7*v_end[ki]*ti -a_end[ki]*ti2,
                               -6*p_start[ki]-3*v_start[ki]*ti-0.5*a_start[ki]*ti2+6*p_end[ki] -3*v_end[ki]*ti +0.5*a_end[ki]*ti2])