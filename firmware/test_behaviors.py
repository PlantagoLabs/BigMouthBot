from BMBLib import setup
from BMBLib import synapse
from BMBLib import behaviors
import asyncio
import time
import math

def find_hot_spot(thermo_cam_image):
    avg_row = 0
    avg_col = 0
    num_samples = 0
    for row_i in range(4):
        for col_i in range(8):
            if thermo_cam_image[row_i][col_i] > 32:
                avg_row += row_i
                avg_col += col_i
                num_samples += 1
    spot_position = []
    if num_samples > 0:
        spot_position = [avg_row/num_samples, avg_col/num_samples]
    print('thermo_cam.hot_spot', num_samples, spot_position)
    synapse.publish('thermo_cam.hot_spot', spot_position, 'find_hot_spot')


def check_nothing():
    return False

def check_hot_spot():
    avg_row = 0
    avg_col = 0
    num_samples = 0
    thermo_cam_image = synapse.recall_message('thermo_cam')

    if thermo_cam_image is None:
        print('no thermo cam')
        return False

    for row_i in range(4):
        for col_i in range(8):
            if thermo_cam_image[row_i][col_i] > 28:
                avg_row += row_i
                avg_col += col_i
                num_samples += 1
    spot_position = []
    if num_samples > 0:
        spot_position = [avg_row/num_samples, avg_col/num_samples]
        return True

    return False

def put_value_in_cache_factory(key, value):
    def put_value_in_cache():
        synapse.memorize(key, value, 'behavior')
    return put_value_in_cache

def save_position_factory(position_name):
    def save_base_position():
        synapse.memorize('behaviors.'+position_name, synapse.recall_message('estimate.pose'), 'behavior')
    return save_base_position

def set_next_target_position():
    new_target_position = synapse.recall_message('behaviors.target_position')
    new_target_position[0] += 500
    synapse.memorize('behaviors.target_position', new_target_position, 'behaviors')

# behavior_list = [behaviors.ChangeCacheBehavior('add_position_in_cache', 
#                                                   put_value_in_cache_factory('behaviors.next_position', [0.0, 0.0]),
#                                                    'find_hot_spot' ),
#                 behaviors.LookFor('find_hot_spot', is_there_tea, 
#                                       ['thermo_cam.hot_spot'], 'say_yay', 
#                                       5000, 'say_no'),
#                 behaviors.SendMessageBehavior('say_yay', lambda cache: ('tunetalk', 'yay', 'behaviors'), [], 'cooldown'),
#                 behaviors.SendMessageBehavior('say_no', lambda cache: ('tunetalk', 'no', 'behaviors'), [], 'cooldown'),
#                 behaviors.SendMessageBehavior('say_aie', lambda cache: ('tunetalk', 'aie', 'behaviors'), [], 'say_hi'),
#                 behaviors.WaitBehavior('cooldown', 400, 'find_hot_spot_cycle')]

# behavior_list = [behaviors.WaitBehavior('initial_wait', 500, 'go_to_point_1'),
#                 behaviors.GoToPointBehavior('go_to_point_1', 1.0, [10, 60], 1.0, 1.0, 'go_to_point_2', [300, 0]),
#                  behaviors.GoToPointBehavior('go_to_point_2', 1.0, [10, 60], 1.0, 1.0, 'go_to_point_3', [100, 200]),
#                  behaviors.GoToPointBehavior('go_to_point_3', 1.0, [10, 60], 1.0, 1.0, 'go_to_point_4', [150, 400]),
#                  behaviors.GoToPointBehavior('go_to_point_4', 1.0, [10, 60], 1.0, 1.0, 'say_yay', [350, 300]),
#                 behaviors.SendMessageBehavior('say_yay', lambda cache: ('tunetalk', 'yay', 'behaviors'), [], 'cooldown'),
#                 behaviors.WaitBehavior('cooldown', 400, 'end'),
#                 behaviors.SendMessageBehavior('say_aie', lambda cache: ('tunetalk', 'aie', 'behaviors'), [], 'end')]

# behavior_list = [behaviors.WaitBehavior('initial_wait', 500, 'go_to_point_1'),
#                 behaviors.GoToHeadingBehavior('go_to_point_1', 1.0, 1.0, 'go_to_point_2', math.radians(60)),
#                  behaviors.GoToHeadingBehavior('go_to_point_2', 1.0, 1.0, 'go_to_point_3', math.radians(-60)),
#                  behaviors.WaitBehavior('middle_wait', 500, 'go_to_point_3'),
#                  behaviors.GoToHeadingBehavior('go_to_point_3', 1.0, 1.0, 'add_position_in_cache', math.radians(240)),
#                  behaviors.ChangeCacheBehavior('add_position_in_cache', 
#                                                   put_value_in_cache_factory('behaviors.next_heading', 0),
#                                                    'go_to_point_4' ),
#                  behaviors.GoToHeadingBehavior('go_to_point_4', 1.0, 1.0, 'say_yay', 'behaviors.next_heading'),
#                 behaviors.SendMessageBehavior('say_yay', lambda cache: ('tunetalk', 'yay', 'behaviors'), [], 'cooldown'),
#                 behaviors.WaitBehavior('cooldown', 400, 'end'),
#                 behaviors.SendMessageBehavior('say_aie', lambda cache: ('tunetalk', 'aie', 'behaviors'), [], 'end')]

init_behavior_list = [behaviors.WaitBehavior('initial_wait', 500, 'add_target_position'),
                    behaviors.CallFunctionOnceBehavior('add_target_position', 
                                                  put_value_in_cache_factory('behaviors.target_position', [0, 0]),
                                                   'add_base_position' ),
                    behaviors.CallFunctionOnceBehavior('add_base_position', 
                                                  save_position_factory('base_position'),
                                                   'move_to_next_position' )]

move_to_next_position_behavior_list = [behaviors.CallFunctionOnceBehavior('set_new_target_position', 
                                                  set_next_target_position,
                                                   'go_to_target' ),
                                        behaviors.GoToPointBehavior('go_to_target', 
                                                                    1.0, [10, 120], 1.0, 1.0, 
                                                                    'scan', 
                                                                    'behaviors.target_position')]

scan_behavior_list = [behaviors.SetVelocityBehavior('scan_rotate', 0, math.radians(60), 'look_for_hot_spot'),
                      behaviors.LookFor('look_for_hot_spot', check_hot_spot, 'stop_scan', 6000, 'say_not_found'),
                      behaviors.SendMessageBehavior('say_not_found', ('tunetalk', 'no', 'behaviors'), 'move_to_next_position'),
                      behaviors.StopBehavior('stop_scan', 'say_found'),
                      behaviors.SendMessageBehavior('say_found', ('tunetalk', 'found', 'behaviors'), 'found_wait'),
                      behaviors.WaitBehavior('found_wait', 1000, 'end')]

eat_jar_behavior_list = [behaviors.CallFunctionOnceBehavior('add_scan_position', 
                                                  save_position_factory('scan_position'),
                                                   'move_to_next_position' )]

task_list = [behaviors.MetaBehavior('init', init_behavior_list, 'initial_wait', []),
             behaviors.MetaBehavior('move_to_next_position', move_to_next_position_behavior_list, 'set_new_target_position', []),
             behaviors.MetaBehavior('scan', scan_behavior_list, 'scan_rotate', []),
            behaviors.MetaBehavior('got_shaken', 
                                     [behaviors.StopBehavior('stop_shaken', 'say_aie'),
                                        behaviors.SendMessageBehavior('say_aie', ('tunetalk', 'aie', 'behaviors'), 'shaken_wait'),
                                     behaviors.WaitBehavior('shaken_wait', 500, 'init')], 'stop_shaken', [])]

trigger_list = [behaviors.EarthQuakeTrigger('shake_trigger', 'got_shaken')]

player = behaviors.Player(behaviors.MetaBehavior('complete_tasks', task_list, 'init', trigger_list))



asyncio.run(player.run())
