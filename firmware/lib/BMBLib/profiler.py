import machine
import time

profiler_data = {'profiles': {}, 'start_time': time.time()}

def reset():
    profiler_data = {'profiles': {}, 'start_time': time.time()}

def profile(tag):
    global profiler_data
    profiler_data['profiles'].setdefault(tag, {'calls': 0, 'time': 0.0})
    def decorator(func):
        def wrapper(*args, **kwargs):
            global profiler_data
            
            t0 = time.ticks_us()
            
            returned_value = func(*args, **kwargs)
            
            tag_data = profiler_data['profiles'].get(tag)
            if tag_data:
                tag_data['calls'] += 1
                tag_data['time'] += time.ticks_diff(time.ticks_us(), t0)/1e6
    
            return returned_value
            
        return wrapper
    return decorator

def get_profiler_data():
    profiler_data['runtime'] = time.time() - profiler_data['start_time']
    return profiler_data