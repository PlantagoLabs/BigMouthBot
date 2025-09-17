from BMBLib import setup
from BMBLib import synapse
from BMBLib import behaviors
from BMBLib import navigation_fields
import asyncio
import time
import math

def put_value_in_cache_factory(key, value):
    def put_value_in_cache():
        synapse.memorize(key, value, 'behavior')
    return put_value_in_cache

target_position_name = 'behaviors.target_position'

def set_target_from_list_factory(targets, ongoing_next_behavior_name, done_next_behavior_name):
    target_counter = 0
    def set_target_from_list():
        nonlocal target_counter
        if target_counter < len(targets):
            synapse.memorize(target_position_name, targets[target_counter], 'behavior')
            synapse.memorize('behavior.next', ongoing_next_behavior_name, 'behavior')
        else:
            synapse.memorize('behavior.next', done_next_behavior_name, 'behavior')
        target_counter += 1
    return set_target_from_list

def make_fields():
    target = synapse.recall_message(target_position_name)[:2]
    return [navigation_fields.GoToPointField(target, 300, 1.0), 
            navigation_fields.ObstaclesField('obstacles', [100, 400], 150, 3)]

synapse.memorize('obstacles', [{'position': [1000, 0]}, {'position': [1000, 600]}], 'custom')

navigator = navigation_fields.DifferentialDriveFieldNavigator(20, 200, 0.5, 1)

task_list = [behaviors.FollowFieldsBehavior('navigate_field', make_fields, 'say_oups', 5000),
            behaviors.SendMessageBehavior('say_oups', ('tunetalk', 'oups', 'behaviors'), 'talk_wait'),
            behaviors.WaitBehavior('talk_wait', 2000, 'end')]

trigger_list = [behaviors.ArrivedAtPositionTrigger('arrived_trigger', target_position_name, 100, 'say_arrived')]

behaviors_list = [behaviors.WaitBehavior('initial_wait', 500, 'add_target_position'),
                behaviors.CallFunctionOnceBehavior('add_target_position',
                                                      set_target_from_list_factory([[2000, 0], [2000, 1000], [0, 0]],
                                                                                   'follow_field',
                                                                                   'end_wait'),
                                                      'choose_behavior'),
                behaviors.ChooseBehaviorFromSynapse('choose_behavior', 'behavior.next'),
                behaviors.MetaBehavior('follow_field', task_list, 'navigate_field', trigger_list),
                  behaviors.SendMessageBehavior('say_arrived', ('tunetalk', 'arrived', 'behaviors'), 'add_target_position'),
                behaviors.WaitBehavior('end_wait', 2000, 'end')]

player = behaviors.Player(behaviors.MetaBehavior('all_behaviors', behaviors_list, 'initial_wait', []))

asyncio.run(player.run())