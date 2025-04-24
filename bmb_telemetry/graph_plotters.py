import tkinter
from abc import ABC, abstractmethod

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

class AbstractFigurePlotter(ABC):
    def __init__(self, tk_master, w, h):
        self.fig = Figure(figsize=(w, h), dpi=100)
        self.fig.subplots_adjust(bottom=0.2)
        self.subplt = self.fig.add_subplot(111)
        self.tk_master = tk_master
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tk_master)  # A tk.DrawingArea.

    def get_tk_widget(self):
        return self.canvas.get_tk_widget()

    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def add_data(self, data):
        pass

class TimelinePlotter(AbstractFigurePlotter):
    def __init__(self, tk_master, max_num_samples = 60., y_lim = None, y_label=None):
        AbstractFigurePlotter.__init__(self, tk_master, 6, 3)
        self.max_num_samples = max_num_samples
        self.y_lim = y_lim
        self.subplt.grid(linestyle=':')
        self.subplt.set_xlabel('Time [s]')
        if y_label:
            self.subplt.set_ylabel(y_label)
        self.data = {}

    def draw(self):
        if not self.data:
            return
        for label in self.data:
            line_data = self.data[label]
            if 'line' not in line_data:
                line_data['line'], = self.subplt.plot(line_data['timestamps'], line_data['samples'], label=label)
                self.subplt.legend()
                
            else:
                line_data['line'].set_xdata(line_data['timestamps'])
                line_data['line'].set_ydata(line_data['samples'])
                self.subplt.set_xlim(line_data['timestamps'][0], line_data['timestamps'][-1] + 0.01)
        
        if self.y_lim:
            self.subplt.set_ylim(self.y_lim)
        else:
            min_val = 1e16
            max_val = -1e16
            for label in self.data:
                line_data = self.data[label]
                max_val = max(max_val, np.max(line_data['samples']))
                min_val = min(min_val, np.min(line_data['samples']))
            self.subplt.set_ylim([min_val, max_val])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events() 
        self.canvas.draw()


    def add_data(self, sample, timestamp, label):
        data = self.data.setdefault(label, {'samples': [], 'timestamps': []})
        data['samples'].append(sample)
        data['timestamps'].append(timestamp)
        if len(data['samples']) > self.max_num_samples:
            data['samples'].pop(0)
            data['timestamps'].pop(0)

class StackedLinePlotter(AbstractFigurePlotter):
    def __init__(self, tk_master, max_num_samples = 60., y_lim = None, y_label=None):
        AbstractFigurePlotter.__init__(self, tk_master, 6, 3)
        self.max_num_samples = max_num_samples
        self.y_lim = y_lim
        self.data = {'stacks': {}, 'timestamps': []}
        self.y_label = y_label

    def draw(self):
        if not self.data['stacks']:
            return
        self.subplt.cla()
        self.subplt.stackplot(self.data['timestamps'], self.data['stacks'].values(), labels=self.data['stacks'].keys())
        if self.y_label:
            self.subplt.set_ylabel(self.y_label)
        self.subplt.legend(loc='upper left')
        self.subplt.grid(linestyle=':')
        self.subplt.set_xlabel('Time [s]')
        if self.y_lim:
            self.subplt.set_ylim(self.y_lim)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events() 
        self.canvas.draw()


    def add_data(self, samples_frame, timestamp, labels):
        for ind, label in enumerate(labels):
            samples = self.data['stacks'].setdefault(label, [])
            samples.append(samples_frame[ind])
            if len(samples) > self.max_num_samples:
                samples.pop(0)
        self.data['timestamps'].append(timestamp)
        if len(self.data['timestamps']) > self.max_num_samples:
            self.data['timestamps'].pop(0)

class GridPlotter(AbstractFigurePlotter):
    def __init__(self, tk_master, c_lim = None):
        AbstractFigurePlotter.__init__(self, tk_master, 6, 6)
        self.c_lim = c_lim
        self.subplt.grid(linestyle=':')
        self.data = {}

    def draw(self):
        if self.data:
            if 'img' not in self.data:
                self.data['img'] = self.subplt.imshow(self.data['array'], cmap='viridis_r')
                if self.c_lim:
                    self.data['img'].set_clim(self.c_lim)
            else:
                self.data['img'].set_data(self.data['array']) 
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events() 
        self.canvas.draw()


    def add_data(self, data):
        try:
            self.data['array'] = np.array(data, dtype=float)
        except:
            print("error in array data")
            print(data)

class PiePlotter(AbstractFigurePlotter):
    def __init__(self, tk_master):
        AbstractFigurePlotter.__init__(self, tk_master, 6, 6)
        self.data = {}

    def draw(self):
        if self.data:
            self.subplt.cla()
            self.subplt.pie(list(self.data.values()), 
                            labels=list(self.data.keys()),
                            startangle=-45,
                            radius=0.5,
                            rotatelabels=True)

        self.canvas.draw()


    def add_data(self, data):
        self.data = data