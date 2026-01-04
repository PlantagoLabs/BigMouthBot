import asyncio
from BMBLib import setup
from BMBLib import synapse
from BMBLib.behaviors import *
from BMBLib.obstacle_map import ObstacleMap
from BMBLib.gridmap import GridMap
from BMBLib import profiler
from BMBLib import sidecore
from BMBLib.behaviors import *
from BMBLib.navigation_fields import DifferentialDriveFieldNavigator, ObstaclesField, InertiaField

### set up obstacle mapping on the second core
obstacle_map = ObstacleMap([-3000, 3000, -3000, 3000], 100)

def update_obstacle_map_on_sidecore(range_data, recalled_data):
    obstacle_map.update_map_with_range_data(range_data, recalled_data['estimate.pose'][1])

def get_obstacle_map(topic_data, recalled_data):
    return obstacle_map.obstacle_scan(recalled_data['estimate.pose'][1])

sidecore.add_task('range_array', update_obstacle_map_on_sidecore, None, ['estimate.pose'])
sidecore.add_task('obstacle_map.start_scan', get_obstacle_map, 'obstacle_map.scan_results', ['estimate.pose'])
sidecore.start()

### link some synapses
synapse.link('memory.status', 'logs')
synapse.memorize('behaviors.base_position', [0, 0], 'behavior')
synapse.subscribe("obstacle_map.lines", setup.link_manager.send_synaptic_mssage)

def getTrue():
    return True
synapse.survey('obstacle_map.start_scan', getTrue, 400, persistent=False)

def split_obstacles_and_unscanned(data):
    synapse.publish('log', f'obstacles data: {data}', 'obstacle_map')
    synapse.publish('obstacle_map.obstacles', data[0], 'obstacle_map')
    synapse.publish('obstacle_map.unsensed', data[1], 'obstacle_map')
synapse.apply('obstacle_map.scan_results', split_obstacles_and_unscanned)

synapse.subscribe('obstacle_map.scan_results', setup.link_manager.send_synaptic_mssage)

### field navigation
def make_fields():
    # return [ObstaclesField('obstacle_map.obstacles', [100, 500], 150, 3),
    #         ObstaclesField('obstacle_map.unsensed', [200, 1500], 50, 1, repulsive=False),
    #         ObstaclesField('obstacle_map.unsensed', [100, 300], 150, 2),
    #         InertiaField(0.5)]
    return [ObstaclesField('obstacle_map.obstacles', [100, 500], 150, 3),
            InertiaField(0.5)]

navigator = DifferentialDriveFieldNavigator(20, 180, 0.3, 0.5)

### make behaviors

class ImminentDangerTrigger(AbstractTrigger):
    def __init__(self, name, obstacle_trig_name, obstacle_line = None, obstacle_range = 300, hole_line = None, hole_range = 300):
        super().__init__(name)
        self.obstacle_trig_name = obstacle_trig_name
        self.obstacle_line = obstacle_line
        self.obstacle_range = obstacle_range
        self.hole_line = hole_line
        self.hole_range = hole_range

    def check(self):
        range_data = synapse.recall_message('range_array')
        if range_data is None:
            return None
        if self.obstacle_line is not None:
            for ki in range(0, 8):
                if range_data[5][ki] is not None and range_data[5][ki] < self.obstacle_range:
                    return self.obstacle_trig_name
        if self.hole_line is not None:
            for ki in range(0, 8):
                if range_data[0][ki] is None or range_data[0][ki] > self.hole_range:
                    return self.obstacle_trig_name
        return None

tasks = [MetaBehavior('init_task', 
                      [WaitBehavior('initial_wait', 500, 'scan_rotate'),
                        SetVelocityBehavior('scan_rotate', 0, math.radians(45), 'scan_wait'),
                        WaitBehavior('scan_wait', 8000, 'navigate_task'),], 
                        'initial_wait', 
                        []),
        MetaBehavior('navigate_task', 
                    [MultiBehavior('multi_navigate',
                                    [FollowFieldsBehavior('navigate_field', make_fields),
                                     MetaBehavior('act_mouth',
                                                   [SetMouthBehavior('open_mouth', 80, 'wait_open'),
                                                    WaitBehavior('wait_open', 500, 'close_mouth'),
                                                    SetMouthBehavior('close_mouth', 10, 'wait_closed'),
                                                    WaitBehavior('wait_closed', 500, 'open_mouth')],
                                                   'open_mouth',
                                                   [])]
                                    )], 
                    'multi_navigate', 
                    [ImminentDangerTrigger('imminent_danger', 'emergency_avoid', obstacle_line=5, obstacle_range=200)]),
        MetaBehavior('emergency_avoid', 
                      [SetVelocityBehavior('avoid_rotate', 0, math.radians(45), 'say_avoiding'),
                       SendMessageBehavior('say_avoiding', ('tunetalk', 'avoiding', 'behaviors'), 'avoid_wait'),
                        WaitBehavior('avoid_wait', 3000, 'navigate_task'),], 
                        'avoid_rotate', 
                        []),
        StopBehavior('final_stop', 'say_stop'),
        SendMessageBehavior('say_stop', ('tunetalk', 'stop', 'behaviors'), 'end')]

### run the behaviors
player = Player(MetaBehavior('complete_tasks', tasks, 'init_task', [TimeTrigger('work_done_timer', 120000, 'final_stop')]))
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


