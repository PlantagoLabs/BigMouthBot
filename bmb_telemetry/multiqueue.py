from queue import Queue
from threading import Lock, Thread
import time
from sys import getrefcount

class MultiQueue:
    def __init__(self):
        self.queues = []
        self.addition_lock = Lock()
        self.running = True
        self.processing_thread = Thread(target=self.__process_queues).start()

    def get_queues(self):
        # to_put, to_get
        new_queues = (Queue(), Queue())
        with self.addition_lock:
            self.queues.append(new_queues)
        return new_queues
    
    def stop(self):
        self.running = False
        self.processing_thread.join()
    
    def __process_queues(self):
        while self.running:
            with self.addition_lock:
                for n, input_queue_pair in enumerate(self.queues):
                    while not input_queue_pair[0].empty():
                        message = input_queue_pair[0].get() # opposite to what the outside code does
                        for k, output_queue_pair in enumerate(self.queues):
                            if n != k:
                                output_queue_pair[1].put(message)
            self.__cleanup()
            time.sleep(0.001)

    def __cleanup(self):
        self.queues = [q for q in self.queues if getrefcount(q[0]) > 2 or getrefcount(q[1]) > 2 ]

multiqueue = MultiQueue()



