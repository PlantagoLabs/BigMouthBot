from array import array
from BMBLib import ulinalg
import time

class GridMap:
    def __init__(self, shape, extent, typecode='B', initial_value = 0):
        self.shape = shape # num row, num col
        self.extent = extent # edges of real work coordinate [min x, max x, min y, max y]
        self.resolution = ((self.extent[1] - self.extent[0])/self.shape[0], (self.extent[3] - self.extent[2])/self.shape[1])
        self.typecode = typecode
        self._data = array(typecode, (initial_value for _ in range(shape[0]*shape[1])))

    def __getitem__(self, coord):
        if not self.is_coordinate_on_grid(coord):
            raise ValueError(f'{coord} is out of bounds')
        
        return self._data[coord[1]*self.shape[0] + coord[0]]
    
    def get_cell_fast(self, coord_x, coord_y):
        return self._data[coord_y*self.shape[0] + coord_x]
    
    def __setitem__(self, coord, value):
        self._data[coord[1]*self.shape[0] + coord[0]] = value

    def get_line(self, line_num):
        return [self[line_num, k] for k in range(self.shape[1])]

    def lines_generator(self):
        line_num = 0
        while line_num < self.shape[0]:
            yield self.get_line(line_num)
            line_num += 1
    
    def world_to_grid(self, position):
        return (round( (position[0] - self.extent[0])/self.resolution[0] ), round( (position[1] - self.extent[2])/self.resolution[1] ))

    def grid_to_world(self, coord):
        return (self.resolution[0]*(coord[0] + 0.5) + self.extent[0], self.resolution[1]*(coord[1] + 0.5) + self.extent[2])

    def is_coordinate_on_grid(self, coord):
        return coord[0] >= 0 and coord[1] >= 0 and coord[0] < self.shape[0] and coord[1] < self.shape[1]
    
    def is_coordinate_pair_on_grid(self, coord_x, coord_y):
        return coord_x >= 0 and coord_y >= 0 and coord_x < self.shape[0] and coord_y < self.shape[1]
    
    def get_square_area_coords(self, center, size):
        coords_in_square = []

        for i in range(-size, size+1):
            for j in range(-size, size+1):
                if self.is_coordinate_on_grid([i + center[0], j + center[1]]):
                    coords_in_square.append([i + center[0], j + center[1]])

        return coords_in_square
    
    def get_row_as_list(self, row_index):
        row_data = []
        for i in range(0, self.shape[1]):
            row_data.append(self[i])
        return row_data
    
    def angle_measure(self, a0, a1, b0, b1):
        dot_a_b = (a0*b0 + a1*b1)
        return ( 100*dot_a_b*dot_a_b )//((a0*a0 + a1*a1)*(b0*b0 + b1*b1))

    def get_cell_line(self, coord_o, coord_d):
        # t0 = time.ticks_us()
        cells_to_reduce = set()

        cox, coy = coord_o
        cdx, cdy = coord_d

        icx = 2*(cox < cdx) - 1
        icy = 2*(coy < cdy) - 1

        cell_x = cox
        cell_y = coy

        # increment_cells = 0
        # is_coordonate_on_grid = 0
        # add_cell_to_line = 0

        # init1 = time.ticks_diff(time.ticks_us(), t0)
        # t0 = time.ticks_us()

        # diff_d_o = [cdx - cox, cdy - coy]
        diff_d_o_x = cdx - cox
        diff_d_o_y = cdy - coy

        # pa = [0, 0]
        # pb = [0, 0]
        # init2 = time.ticks_diff(time.ticks_us(), t0)

        while not (cell_x == cdx and cell_y == cdy):
            # t0 = time.ticks_us()
            pax = cell_x + icx - cox
            pay = cell_y - coy
            pbx = cell_x - cox
            pby = cell_y + icy - coy
            # increment_cells = time.ticks_diff(time.ticks_us(), t0)
            # t0 = time.ticks_us()
            # if ulinalg.cosine_2d_sq(pa, diff_d_o) > ulinalg.cosine_2d_sq(pb, diff_d_o):
            if self.angle_measure(pax, pay, diff_d_o_x, diff_d_o_y) > self.angle_measure(pbx, pby, diff_d_o_x, diff_d_o_y):
                cell_x += icx
            else:
                cell_y += icy

            cell = (cell_x, cell_y)
            
            if not self.is_coordinate_on_grid(cell):
                break

            # is_coordonate_on_grid = time.ticks_diff(time.ticks_us(), t0)
            # t0 = time.ticks_us()

            self[cell] += 1
            if self[cell] > 200:
                cells_to_reduce.add(cell)

            # cells_in_line.add( cell )

            # add_cell_to_line = time.ticks_diff(time.ticks_us(), t0)
           
        # print(len(cells_in_line), init1, init2, increment_cells, is_coordonate_on_grid, add_cell_to_line)

        return cells_to_reduce
    
    def increment_cells(self, cells, value = 1):
        for cell in cells:
            if self.is_coordinate_on_grid(cell):
                self[cell] += value
