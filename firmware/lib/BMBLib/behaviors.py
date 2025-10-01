import asyncio
from BMBLib import synapse
from BMBLib import ulinalg
import time
import random
import math

class Player:
    """Takes one behavior and and plays it in an async loop.
    
    Use the MultiBehavior class to run a state machine with multiple behaviors."""
    def __init__(self, behavior, period_ms = 100, ):
        self.period_ms = period_ms
        self.synaptic_cache = {}
        self.followed_topics = set()
        self.behavior = behavior

    async def run(self):
        self.behavior.start()
        while 1:
            await asyncio.sleep_ms(self.period_ms)
            try:
                returned_name = self.behavior.play()
            except StopIteration:
                print('Done playing behavior')
                break
            except Exception as e:
                raise e
            if returned_name is not None:
                # print(f'switching to {new_behavior_name}')
                # synapse.publish('log', f'switching to {new_behavior_name}', 'behavior')
                print(f'Behavior returned {returned_name} stopping')
                self.behavior.stop()
                break

##### Behaviors ######

class AbstractBehavior:
    def __init__(self, name):
        self.name = name
        
    def start(self):
        """Called once when this behavior is activated"""
        pass

    def play(self):
        """Called periodically while this behavior is active"""
        return None
    
    def stop(self):
        """Called once when this behavior is deactivated"""
        pass

class MetaBehavior(AbstractBehavior):
    """Behavior that can switch between behaviors it is provide, based on name. Only plays a simgle behavior at the time"""
    def __init__(self, name, list_of_behaviors, starting_behavior_name, triggers = (), log_switching = False):
        self.name = name
        self.behaviors = {behavior.name: behavior for behavior in list_of_behaviors}
        self.triggers = triggers
        self.starting_behavior_name = starting_behavior_name
        self.log_switching = log_switching

    def start(self):
        self.behaviors[self.starting_behavior_name].start()
        self.current_behavior_name = self.starting_behavior_name

    def play(self):
        new_behavior_name = None
        for trigger in self.triggers:
            new_behavior_name = trigger.check()
            if new_behavior_name:
                break
        if new_behavior_name is None:
            new_behavior_name = self.behaviors[self.current_behavior_name].play()
        if new_behavior_name is not None:
            synapse.publish('log', f'switching to {new_behavior_name}', f'behavior.{self.name}')
            if new_behavior_name in self.behaviors:
                self.behaviors[self.current_behavior_name].stop()
                self.behaviors[new_behavior_name].start()
                self.current_behavior_name = new_behavior_name
            else:
                return new_behavior_name
            
    def stop(self):
        self.behaviors[self.current_behavior_name].stop()
            
class MultiBehavior(AbstractBehavior):
    """Behavior that can play several behaviors at the same time. It will stop as soon one of the inner behaviors calls for a change"""
    def __init__(self, name, list_of_behaviors):
        self.name = name
        self.behaviors = list_of_behaviors
    def start(self):
        for behavior in self.behaviors:
            behavior.start()

    def start(self):
        for behavior in self.behaviors:
            behavior.play()

    def stop(self):
        for behavior in self.behaviors:
            behavior.stop()

    
class SendMessageBehavior(AbstractBehavior):
    def __init__(self, name, synaptic_tuple, next_behavior_name):
        self.name = name
        self.synaptic_tuple = synaptic_tuple
        self.next_behavior_name = next_behavior_name

    def play(self):
        synapse.publish(*self.synaptic_tuple)
        return self.next_behavior_name
    
class CallFunctionOnceBehavior(AbstractBehavior):
    def __init__(self, name, function, next_behavior_name):
        self.name = name
        self.function = function
        self.next_behavior_name = next_behavior_name

    def play(self):
        self.function()
        return self.next_behavior_name
    
class ChooseBehaviorFromSynapse(AbstractBehavior):
    def __init__(self, name, next_behavior_key):
        self.name = name
        self.next_behavior_key = next_behavior_key

    def play(self):
        return synapse.recall_message(self.next_behavior_key)

class WaitBehavior(AbstractBehavior):
    def __init__(self, name, wait_time_ms, next_behavior_name):
        self.name = name
        self.wait_time_ms = wait_time_ms
        self.next_behavior_name = next_behavior_name

    def start(self):
        self.start_ticks_ms = time.ticks_ms()

    def play(self):
        if time.ticks_diff(time.ticks_ms(), self.start_ticks_ms) > self.wait_time_ms:
            return self.next_behavior_name
        else:
            return None
        
class WaitForMessageBehavior(AbstractBehavior):
    def __init__(self, name, topic, next_behavior_name, erase_after_reception = False):
        self.name = name
        self.topic = topic
        self.next_behavior_name = next_behavior_name
        self.erase_after_reception = erase_after_reception

    def play(self):
        if synapse.recall_message(self.topic) is not None:
            return self.next_behavior_name
        return None
    
    def stop(self):
        if self.erase_after_reception:
            synapse.forget(self.topic)
        
class ExitBehavior(AbstractBehavior):
    def __init__(self, name):
        self.name = name

    def play(self):
        raise StopIteration

class StopBehavior(AbstractBehavior):
    def __init__(self, name, next_behavior_name):
        self.name = name
        self.next_behavior_name = next_behavior_name

    def start(self):
        synapse.publish('drivetrain.stop', None, 'behavior')

    def play(self):
        return self.next_behavior_name
    
class FollowFieldsBehavior(AbstractBehavior):
    def __init__(self, name, fields, next_behavior_name, timeout_ms=-1):
        self.name = name
        self.fields_proto = fields
        self.next_behavior_name = next_behavior_name

    def start(self):
        if callable(self.fields_proto):
            self.fields = self.fields_proto()
        else:
            self.fields = self.fields_proto

        synapse.publish('navigator.fields', self.fields, 'behavior')

    def play(self):
        return None
    
    def stop(self):
        synapse.publish('navigator.deactivate', None, 'behavior')

class SetVelocityBehavior(AbstractBehavior):
    def __init__(self, name, speed, yaw_rate, next_behavior_name):
        self.name = name
        self.speed = speed
        self.yaw_rate = yaw_rate
        self.next_behavior_name = next_behavior_name

    def start(self):
        synapse.publish('drivetrain.set_velocity', {'forward_speed': self.speed, 'yaw_rate': self.yaw_rate}, 'behavior')

    def play(self):
        return self.next_behavior_name
    
class GoToPointBehavior(AbstractBehavior):
    def __init__(self, name, speed_gain, speed_range, angle_gain, angle_max_speed, next_behavior_name, target = 'behavior.position'):
        self.name = name
        self.speed_gain = speed_gain
        self.speed_range = speed_range
        self.angle_gain = angle_gain
        self.angle_max_speed = angle_max_speed
        self.target = target
        self.next_behavior_name = next_behavior_name

    def start(self):
        self.start_point = synapse.recall_message('estimate.pose')[:2]
        if isinstance(self.target, str):
            self.end_point = synapse.recall_message(self.target)
        else:
            self.end_point = self.target
        self.initial_goal_vector = ulinalg.diff_vector(self.end_point, self.start_point)

    def play(self):
        current_position = synapse.recall_message('estimate.pose')[:2]
        vector_to_goal = ulinalg.diff_vector(self.end_point, current_position)
        if ulinalg.dot(vector_to_goal, self.initial_goal_vector) < 0:
            return self.next_behavior_name

        goal_heading = ulinalg.heading(vector_to_goal)
        diff_heading = goal_heading - synapse.recall_message('estimate.pose')[2]
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
        print(current_position, ulinalg.dot(vector_to_goal, self.initial_goal_vector),
               diff_heading, self.angle_gain*diff_heading, ulinalg.norm(vector_to_goal), target_speed)
        synapse.publish('drivetrain.set_velocity', {'forward_speed': target_speed, 
                                                    'yaw_rate': angle_speed}, 'behavior')
        return None

    def stop(self):
        synapse.publish('drivetrain.stop', None, 'behavior')
    
class GoToHeadingBehavior(AbstractBehavior):
    def __init__(self, name, angle_gain, angle_max_speed, next_behavior_name, target = 'behavior.position'):
        self.name = name
        self.angle_gain = angle_gain
        self.angle_max_speed = angle_max_speed
        self.target = target
        self.target_heading = None
        self.next_behavior_name = next_behavior_name

    def start(self):
        if isinstance(self.target, str):
            self.target_heading = synapse.recall_message(self.target)
        else:
            self.target_heading = self.target

    def play(self):
        diff_heading = self.target_heading - synapse.recall_message('estimate.pose')[2]
        print(self.target_heading, synapse.recall_message('estimate.pose')[2], diff_heading)
        while diff_heading > math.pi:
            diff_heading -= 2*math.pi
        while diff_heading < -math.pi:
            diff_heading += 2*math.pi

        if abs(diff_heading) < 0.03:
            return self.next_behavior_name

        angle_speed = self.angle_gain*diff_heading + math.copysign(0.05, diff_heading)
        if angle_speed > self.angle_max_speed:
            angle_speed = self.angle_max_speed
        elif angle_speed < -self.angle_max_speed:
            angle_speed = -self.angle_max_speed

        print(diff_heading, angle_speed)

        synapse.publish('drivetrain.set_velocity', {'forward_speed': 0.0, 
                                                    'yaw_rate': angle_speed}, 'behavior')
        
        return None

    def stop(self):
        synapse.publish('drivetrain.stop', None, 'behavior')
    
class SetMouthBehavior(AbstractBehavior):
    def __init__(self, name, angle, next_behavior_name):
        self.name = name
        self.angle = angle
        self.next_behavior_name = next_behavior_name

    def start(self):
        if self.angle is not None:
            synapse.publish('mouth.angle', self.angle, 'behavior')
        else:
            synapse.publish('mouth.free', None, 'behavior')

    def play(self):
        return self.next_behavior_name
    
class LookFor(AbstractBehavior):
    def __init__(self, name, decision_function, if_true_behavior_name, timeout_ms=-1, timeout_behavior_name=None):
        self.name = name
        self.decision_function = decision_function
        self.if_true_behavior_name = if_true_behavior_name
        self.timeout_ms = timeout_ms
        self.timeout_behavior_name = timeout_behavior_name

    def start(self):
        self.start_ticks_ms = time.ticks_ms()

    def play(self):
        if self.decision_function():
            return self.if_true_behavior_name
        if self.timeout_ms > 0 and time.ticks_diff(time.ticks_ms(), self.start_ticks_ms) > self.timeout_ms:
            return self.timeout_behavior_name
        return None

    
class RandomBehavior(AbstractBehavior):
    def __init__(self, name, list_random_behaviors):
        self.name = name
        self.list_random_behaviors = list_random_behaviors

    def play(self):
        return random.choice(self.list_random_behaviors)
    
##### Triggers ######

class AbstractTrigger:
    def __init__(self, name):
        self.name = name
        
    def check(self):
        """Returns a behavior name if trigger condition is met"""
        return None
    
class EarthQuakeTrigger(AbstractTrigger):
    def __init__(self, name, triggered_behavior_name):
        self.name = name
        self.triggered_behavior_name = triggered_behavior_name
        
    def check(self):
        if abs(synapse.recall_message('imu')['acc'][0]) > 150 or abs(synapse.recall_message('imu')['acc'][1]) > 150:
            return self.triggered_behavior_name
        return None
    

class ArrivedAtPositionTrigger(AbstractTrigger):
    """Trigger a behavior when estimate position is reached.
    
    Arguments are:
    - name: name of the trigger
    - target_position: if a list/tuple, it will be used directly as position, if a string, it will be used as key to recall a position
    - radius: radius of the target
    - triggered_behavior_name: name of triggered behavior"""
    def __init__(self, name, target_position, radius, triggered_behavior_name):
        self.name = name
        self.target_position = target_position
        self.radius = radius
        self.triggered_behavior_name = triggered_behavior_name

    def check(self):
        current_position = synapse.recall_message('estimate.pose')[:2]
        if isinstance(self.target_position, str):
            target = synapse.recall_message(self.target_position)
            if target is None:
                return None
            target = target[:2]
        else:
            target = self.target_position
        distance = ulinalg.norm_sq(ulinalg.diff_vector(current_position, target))
        if distance < self.radius**2:
            return self.triggered_behavior_name

        return None
