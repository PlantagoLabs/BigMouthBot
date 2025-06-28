import asyncio
from BMBLib import synapse

class AbstractBehavior:
    def __init__(self, name):
        self.name = name
        
    def start(self):
        pass

    def play(self):
        return None
    
    def stop(self):
        pass

    def required_topics(self):
        return []
    
    def set_synaptic_cache(self, synaptic_cache):
        self.synaptic_cache = synaptic_cache

class Player:
    def __init__(self, period_ms = 100):
        self.period_ms = period_ms
        self.synaptic_cache = {}
        self.followed_topics = set()
        self.behaviors = {}
        self.current_behavior_name = None

    def add_behavior(self, behavior):
        for topic in behavior.required_topics():
            if topic not in self.followed_topics:
                synapse.subscribe(topic, self._update_synaptic_cache)
                self.followed_topics.add(topic)
        behavior.set_synaptic_cache(self.synaptic_cache)
        self.behaviors[behavior.name] = behavior

    async def run(self, starting_behavior_name):
        self.current_behavior_name = starting_behavior_name
        self.behaviors[self.current_behavior_name].start()
        while 1:
            await asyncio.sleep_ms(self.period_ms)
            new_behavior_name = self.behaviors[self.current_behavior_name].play()
            if new_behavior_name is not None:
                self.behaviors[self.current_behavior_name].stop()
                self.behaviors[new_behavior_name].start()
                self.current_behavior_name = new_behavior_name

    def _update_synaptic_cache(self, topic, message, source):
        self.synaptic_cache[topic] = message