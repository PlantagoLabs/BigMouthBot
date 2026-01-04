import asyncio
from BMBLib import setup
from BMBLib import synapse
from BMBLib.behaviors import *
from BMBLib.obstacle_map import ObstacleMap
from BMBLib.gridmap import GridMap
from BMBLib import profiler
from BMBLib import sidecore
from BMBLib import behaviors
from BMBLib import navigation_fields

### set up obstacle mapping on the second core
obstacle_map = ObstacleMap([-2000, 4000, -3000, 3000], 100)
# obstacle_map.set_enable_map(False)

# test_grid = GridMap([20, 20], [-4000,  4000, -4000, 4000])

def update_obstacle_map_on_sidecore(range_data, recalled_data):
    obstacle_map.update_map_with_range_data(range_data, recalled_data['estimate.pose'][1])

# range_array_link_switch = synapse.SwitchLink('range_array', 'range_array.switched', 'range_array.switched.enable')

sidecore.add_task('range_array', update_obstacle_map_on_sidecore, None, ['estimate.pose'])
sidecore.start()

### link some synapses

synapse.link('memory.status', 'logs')
synapse.memorize('behaviors.target_position', [0, 0], 'behavior')
synapse.subscribe("obstacle_map.lines", setup.link_manager.send_synaptic_mssage)

### prepare logic to change targets

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

### field navigation

def make_fields():
    target = synapse.recall_message(target_position_name)[:2]
    return [navigation_fields.GoToPointField(target, 300, 1.0)]

navigator = navigation_fields.DifferentialDriveFieldNavigator(20, 200, 0.5, 1)

### make behaviors

navigate_list = [behaviors.FollowFieldsBehavior('navigate_field', make_fields),
            behaviors.SendMessageBehavior('say_oups', ('tunetalk', 'oups', 'behaviors'), 'talk_wait'),
            behaviors.WaitBehavior('talk_wait', 2000, 'end')]

trigger_list = [behaviors.ArrivedAtPositionTrigger('arrived_trigger', target_position_name, 100, 'say_arrived')]

behaviors_list = [behaviors.WaitBehavior('initial_wait', 500, 'scan_rotate'),
                  behaviors.SetVelocityBehavior('scan_rotate', 0, math.radians(45), 'scan_wait'),
                  behaviors.WaitBehavior('scan_wait', 8000, 'add_target_position'),
                behaviors.CallFunctionOnceBehavior('add_target_position',
                                                      set_target_from_list_factory([[0, -1000], [0, -500], [500, 500], [1000, 0], 
                                                                                    [2200, -300], [1500, 0], [2000, 0],
                                                                                     [2800, 500], [2500, 0], [500, 0], [0, 0]],
                                                                                   'follow_field',
                                                                                   'end_stop'),
                                                      'choose_behavior'),
                behaviors.ChooseBehaviorFromSynapse('choose_behavior', 'behavior.next'),
                behaviors.MetaBehavior('follow_field', navigate_list, 'navigate_field', trigger_list),
                  behaviors.SendMessageBehavior('say_arrived', ('tunetalk', 'arrived', 'behaviors'), 'scan_rotate'),
                  behaviors.StopBehavior('end_stop', 'end_wait'),
                behaviors.WaitBehavior('end_wait', 2000, 'end')]

### run the behaviors
player = behaviors.Player(behaviors.MetaBehavior('complete_tasks', behaviors_list, 'initial_wait', []))
asyncio.run(player.run())

### stop and send resulting map
sidecore.stop_and_join()

async def send_data():
    for k in range(obstacle_map.occupancy_map.shape[0]):
        line = obstacle_map.get_data_line(k)
        synapse.publish("obstacle_map.lines", line, 'test')
        print(line)
        await asyncio.sleep_ms(100)

    await asyncio.sleep_ms(2000)

asyncio.run(send_data())

print('All done')