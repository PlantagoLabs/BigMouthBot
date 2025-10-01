from BMBLib import ulinalg
import math
from BMBLib.gridmap import GridMap
from BMBLib import synapse
from BMBLib import profiler
import time

class ObstacleMap:
    def __init__(self, world_extent, resolution, reduce_above = 200):
        self.world_extent = world_extent
        self.resolution = resolution
        self.reduce_above = reduce_above
        self.grid_size = [round( (self.world_extent[1] - self.world_extent[0])/self.resolution ), 
                          round( (self.world_extent[3] - self.world_extent[2])/self.resolution )]
        self.robot_state = None
        self.ray_bearing = (-0.31415927, -0.22439948, -0.13463969, -0.0448799, 0.0448799, 0.13463969, 0.22439948, 0.31415927)
        self.layers_to_use = (5,)

        self.occupancy_map = GridMap(self.grid_size, self.world_extent)
        self.sensed_map = GridMap(self.grid_size, self.world_extent)

    # @profiler.profile("obstacle_map.update")
    def update_map_with_range_data(self, range_data, robot_state):

        cells_to_reduce = set()

        robot_cell = self.occupancy_map.world_to_grid(robot_state[:2])
        
        for ki in range(0, 8):
            total_dist = 0
            sample_count = 0
            was_none = True
            for layer in self.layers_to_use:
                dist = range_data[layer][ki] 
                if dist is not None and dist < 250:
                    was_none = False
                    continue

                if dist is not None:
                    was_none = False
                    total_dist += dist
                    sample_count += 1

            if was_none:
                total_dist = 800
            elif sample_count > 0:
                total_dist //= sample_count
            else:
                continue
            
            total_dist += 120 # distance between sensor and wheel axle, not quite right
            point = [robot_state[0] + total_dist*math.cos(robot_state[2] - self.ray_bearing[ki]),
                    robot_state[1] + total_dist*math.sin(robot_state[2] - self.ray_bearing[ki])]

            cell = self.occupancy_map.world_to_grid(point)

            if not was_none:
                if self.occupancy_map.is_coordinate_on_grid(cell):
                    self.occupancy_map[cell] += 1
                    if self.occupancy_map[cell] > 200:
                        cells_to_reduce.add(cell)

            cells_to_reduce |= self.sensed_map.get_cell_line(robot_cell, cell)

        for cell in cells_to_reduce:
            self.sensed_map[cell] = self.sensed_map[cell]>>1
            self.occupancy_map[cell] = self.occupancy_map[cell]>>1

    def get_data_line(self, line_number):
        if line_number >= self.occupancy_map.shape[0]:
            return None
        line_data = {'line_number': line_number,
                    'sensed': self.sensed_map.get_line(line_number),
                     'occupancy': self.occupancy_map.get_line(line_number)}
        return line_data

    def square_occupancy_stats(self, world_position, square_size):
        center_coord = self.occupancy_map.world_to_grid(world_position)
        square_cells = self.occupancy_map.get_square_area_coords(center_coord, square_size)

        num_occupied = 0
        num_sensed = 0
        pressure = 0.0
        force = [0.0, 0.0]

        for cell in square_cells:
            if self.sensed_map[cell] > 20:
                num_sensed += 1
            elif self.occupancy_map[cell]/(self.sensed_map[cell] + 1):
                num_occupied += 1

        return (num_sensed/len(square_cells), num_occupied/len(square_cells), pressure, force)


        
                


