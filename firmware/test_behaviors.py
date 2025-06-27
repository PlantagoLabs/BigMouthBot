from BMBLib import setup
from BMBLib import synapse
from BMBLib.behavior import AbstractBehavior, Player
import asyncio
import time

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

player = Player()

player.add_behavior(WaitBehavior('starting_wait', 500,'go_straight' ))
player.add_behavior(SetVelocityBehavior('go_straight', 80, 0,'1s_go_straight' ))
player.add_behavior(WaitBehavior('1s_go_straight', 1000, 'turn'))
player.add_behavior(SetVelocityBehavior('turn', 0, 0.8, '1s_turn'))
player.add_behavior(WaitBehavior('1s_turn', 1000, 'go_straight'))

asyncio.run(player.run('starting_wait'))
