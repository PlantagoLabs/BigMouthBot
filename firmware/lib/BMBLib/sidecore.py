import _thread
from BMBLib import synapse
import asyncio
import time

_running = False
_done = False
_tasks = []
_lock = _thread.allocate_lock()

def add_task(input_topic, method, output_topic, to_recall):
    global _running
    global _tasks
    if _running:
        raise RuntimeError('Not allowed to ask tasks while the second core is _running')
    _tasks.append( {'input_topic': input_topic, 'method': method, 'output_topic': output_topic,
                        'to_recall': to_recall, 'input': None, 'output': None} )
    synapse.subscribe(input_topic, _receive_data)
    
def _run_tasks():
    global _running
    global _done
    global _tasks
    while _running:
        for task in _tasks:
            input = None
            with _lock:
                if task['input'] is not None and task['output'] is None:
                    input = task['input']
            if input:
                output = task['method'](*input)
            with _lock:
                if task['output_topic'] and output:
                    task['output'] = output
                task['input'] = None
    _done = True

def _receive_data(topic, message, source):
    global _tasks
    for task in _tasks:
        if topic == task['input_topic'] and task['input'] is None:
            recalled = {to_recall: synapse.recall(to_recall) for to_recall in task['to_recall']}
            with _lock:
                task['input'] = (message, recalled)

async def _send_data():
    global _tasks
    while True:
        for task in _tasks:
            with _lock:
                if task['output'] is not None:
                    synapse.publish(task['output_topic'], task['output'], 'sidecore')
                    task['output'] = None
        await asyncio.sleep_ms(30)

def start():
    global _running
    global _tasks
    if _running:
        raise RuntimeError('Sidecore is already _running, please stop it first')
    _running = True
    thread_id = _thread.start_new_thread(_run_tasks, tuple())

def stop_and_join():
    global _running
    global _done
    _running = False
    while not _done:
        time.sleep_ms(10)
    _done = False
    
asyncio.create_task(_send_data())