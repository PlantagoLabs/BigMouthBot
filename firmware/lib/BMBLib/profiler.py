import machine
import time

profiler_data = {'profiles': {}, 'start_time': time.time()}

def reset():
    global profiler_data
    profiler_data = {'profiles': {}, 'start_time': time.time()}

def profile(tag):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global profiler_data
            
            t0 = time.ticks_us()
            
            returned_value = func(*args, **kwargs)
            
            tag_data = profiler_data['profiles'].setdefault(tag, {'calls': 0, 'time': 0.0})
            if tag_data:
                tag_data['calls'] += 1
                tag_data['time'] += time.ticks_diff(time.ticks_us(), t0)/1e6
    
            return returned_value
            
        return wrapper
    return decorator

def get_profiler_data():
    profiler_data['runtime'] = time.time() - profiler_data['start_time']
    return profiler_data

class TimeIt:
    def __init__(self, tag = 'TimeIt'):
        self.tag = tag

    def __enter__(self):
        self.t0 = time.ticks_us()

    def __exit__(self, exc_type, exc_value, traceback):
        print('Time ellapsed for {}: {} s'.format(self.tag, time.ticks_diff(time.ticks_us(), self.t0)/1e6))