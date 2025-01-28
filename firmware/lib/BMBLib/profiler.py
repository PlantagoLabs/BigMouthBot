import machine
import time

profiler_data = {}

def register_tags(tags):
    global profiler_data
    for tag in tags:
        profiler_data.setdefault(tag, {'calls': 0, 'time': 0.0})

def profile(tag):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global profiler_data
            
            t0 = time.ticks_us()
            
            returned_value = func(*args, **kwargs)
            
            tag_data = profiler_data.get(tag)
            if tag_data:
                tag_data['calls'] += 1
                tag_data['time'] += time.ticks_diff(time.ticks_us(), t0)/1e6
    
            return returned_value
            
        return wrapper
    return decorator

def get_profiler_data():
    return profiler_data