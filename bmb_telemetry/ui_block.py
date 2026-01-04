import tkinter
from tkinter.scrolledtext import ScrolledText
from abc import ABC, abstractmethod

import graph_plotters

class UIGrid:
    def __init__(self, tk_master, width, block_names):
        self.ui_blocks = []
        self.tk_master = tk_master

        row_num = 0
        col_num = 0
        for block_name in block_names:
            block = self.__build_block(block_name)
            block.get_main_tk_frame().grid(row=row_num, column=col_num)
            self.ui_blocks.append(block)
            col_num += 1
            if col_num >= width:
                col_num = 0
                row_num += 1

    def __build_block(self, block_name):
        if block_name == 'memory':
            return MemoryBlock(self.tk_master)
        elif block_name == 'imu':
            return IMUBlock(self.tk_master)
        elif block_name == 'bat_and_line':
            return BatAndLineBlock(self.tk_master)
        elif block_name == 'range_array':
            return RangeArrayBlock(self.tk_master) 
        elif block_name == 'thermo_cam':
            return ThermoCamBlock(self.tk_master) 
        elif block_name == 'cpu':
            return CPUBlock(self.tk_master)     
        elif block_name == 'trajectory':
            return TrajectoryBlock(self.tk_master)  
        elif block_name == 'log':
            return LogBox(self.tk_master)  
        
    def update_blocks_with_messages(self, messages):
        for block in self.ui_blocks:
            block.process_messages(messages)


class AbstractUIBlock(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def process_messages(self, messages):
        pass

    @abstractmethod
    def get_main_tk_frame(self):
        pass

class IMUBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.imu_frame = tkinter.Frame(tk_master)
        self.acc_timeline = graph_plotters.TimelinePlotter(self.imu_frame, max_num_samples = 300, y_label='Acceleration [?]')
        self.acc_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.acc_timeline.draw()
        self.gyro_timeline = graph_plotters.TimelinePlotter(self.imu_frame, max_num_samples = 300, y_label='Rotation Speed [?]')
        self.gyro_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.gyro_timeline.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'imu':
                self.acc_timeline.add_data(data['message']['acc'][0], data['timestamp'], 'x')
                self.acc_timeline.add_data(data['message']['acc'][1], data['timestamp'], 'y')
                self.acc_timeline.add_data(data['message']['acc'][2], data['timestamp'], 'z')
                self.gyro_timeline.add_data(data['message']['gyro'][0], data['timestamp'], 'x')
                self.gyro_timeline.add_data(data['message']['gyro'][1], data['timestamp'], 'y')
                self.gyro_timeline.add_data(data['message']['gyro'][2], data['timestamp'], 'z')
                redraw = True
        
        if redraw:
            self.acc_timeline.draw()
            self.gyro_timeline.draw()

    def get_main_tk_frame(self):
        return self.imu_frame
    

class MemoryBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()
        self.memory_frame = tkinter.Frame(tk_master)
        self.ram_timeline = graph_plotters.StackedLinePlotter(self.memory_frame, y_label='RAM [kB]')
        self.ram_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.ram_timeline.draw()
        self.storage_timeline = graph_plotters.StackedLinePlotter(self.memory_frame, y_label='Storage [Nodes]')
        self.storage_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.storage_timeline.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'memory':
                redraw = True
                for label in data['message']['ram']:
                    data['message']['ram'][label] = data['message']['ram'][label]/1e3
                self.ram_timeline.add_data(list(data['message']['ram'].values()), data['timestamp'], list(data['message']['ram'].keys()))
                self.storage_timeline.add_data(list(data['message']['storage'].values()), data['timestamp'], list(data['message']['storage'].keys()))

        if redraw:
            self.ram_timeline.draw()
            self.storage_timeline.draw()

    def get_main_tk_frame(self):
        return self.memory_frame

class BatAndLineBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.sensor_frame = tkinter.Frame(tk_master)
        self.v_batt_timeline = graph_plotters.TimelinePlotter(self.sensor_frame, y_lim=[3.6, 6.0], y_label='Voltage [V]')
        self.v_batt_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.v_batt_timeline.draw()
        self.reflect_timeline = graph_plotters.TimelinePlotter(self.sensor_frame, y_lim=[0, 1], y_label='Reflectance [-]')
        self.reflect_timeline.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.reflect_timeline.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'v_batt':
                self.v_batt_timeline.add_data(data['message'], data['timestamp'], 'v_batt')
                redraw = True
            elif 'reflect' in data['topic']:
                self.reflect_timeline.add_data(data['message'], data['timestamp'], data['topic'])
                redraw = True

        if redraw:
            self.v_batt_timeline.draw()
            self.reflect_timeline.draw()

    def get_main_tk_frame(self):
        return self.sensor_frame

class TrajectoryBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.trajectory_plotter = graph_plotters.TrajectoryPlotter(tk_master)
        self.trajectory_plotter.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'estimate.pose':
                self.trajectory_plotter.add_data(data['message'])
                redraw = True

        if redraw:
            self.trajectory_plotter.draw()

    def get_main_tk_frame(self):
        return self.trajectory_plotter.get_tk_widget()

class EncoderBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

    def process_messages(self, messages):
        print('not implemented')

    def get_main_tk_frame(self):
        pass

class RangeArrayBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.range_array_img = graph_plotters.GridPlotter(tk_master, c_lim=[0, 2000])
        self.range_array_img.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'range_array':
                self.range_array_img.add_data(data['message'])
                redraw = True

        if redraw:
            self.range_array_img.draw()

    def get_main_tk_frame(self):
        return self.range_array_img.get_tk_widget()
    
class ThermoCamBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.thermo_cam_img = graph_plotters.GridPlotter(tk_master, c_lim=[0, 60], cmap='plasma')
        self.thermo_cam_img.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'thermo_cam':
                self.thermo_cam_img.add_data(data['message'])
                redraw = True

        if redraw:
            self.thermo_cam_img.draw()

    def get_main_tk_frame(self):
        return self.thermo_cam_img.get_tk_widget()

class CPUBlock(AbstractUIBlock):
    def __init__(self, tk_master):
        super().__init__()

        self.cpu_usage_img = graph_plotters.PiePlotter(tk_master)
        self.cpu_usage_img.draw()

    def process_messages(self, messages):
        redraw = False
        for data in messages:
            if data['topic'] == 'cpu_profile':
                profiles = {}
                total_time_usage = 0
                for profile_name in data['message']['profiles']:
                    profile_time = data['message']['profiles'][profile_name]['time']
                    total_time_usage += profile_time
                    if profile_time/(data['message']['runtime']+0.01) > 0.03: 
                        profiles[profile_name] = profile_time
                    else:
                        profiles.setdefault('other', 0)
                        profiles['other'] += profile_time
                profiles['idle'] = max(data['message']['runtime'] - total_time_usage, 0.1)
                self.cpu_usage_img.add_data(profiles)
                redraw = True

        if redraw:
            self.cpu_usage_img.draw()

    def get_main_tk_frame(self):
        return self.cpu_usage_img.get_tk_widget()
    
class LogBox(AbstractUIBlock):
    def __init__(self, tk_master, topics_to_log = ('log',)):
        super().__init__()
        self.text_frame = ScrolledText(master=tk_master, width=60,  height=24)
        self.data = ""
        self.topics_to_log = topics_to_log

    def process_messages(self, messages):
        for message in messages:
            if message['topic'] in self.topics_to_log:
                self.text_frame.insert('end', '\n' + str(message['message']))

    def get_main_tk_frame(self):
        return self.text_frame
