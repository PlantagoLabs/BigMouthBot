import asyncio

_channels = {}

def _get_channel(topic):
    return _channels.setdefault(topic, {'subs': [], 'persisted': None})

def subscribe(topic, callback):
    channel = _get_channel(topic)
    channel['subs'].append(callback)

    if channel['persisted'] is not None:
        callback(*channel['persisted'])

def unsubscribe(topic, callback):
    channel = _get_channel(topic)
    channel['subs'] = [sub for sub in channel['subs'] if sub != callback]

def publish(topic, message, source = None, persistent = True):
    channel = _get_channel(topic)

    if persistent:
        channel['persisted'] = (topic, message, source)

    for sub in channel['subs']:
        sub(topic, message, source)

async def _survey_task(topic, msg_function, period_ms, source, persistent):
    while 1:
        data = msg_function()
        if data is not None:
            publish(topic, data, source, persistent)
        await asyncio.sleep_ms(period_ms)

def survey(topic, msg_function, period_ms, source = None, persistent = True):
    asyncio.create_task(_survey_task(topic, msg_function, period_ms, source, persistent))

def apply(topic, act_function):
    subscribe(topic, lambda x, y, z: act_function(y) if y is not None else act_function())

def link(topic_in, topic_out):
    subscribe(topic_in, lambda x, y, z: publish(topic_out, y, z))

def memorize(topic, message, source):
    channel = _get_channel(topic)
    channel['persisted'] = (topic, message, source)

def recall(topic):
    channel = _get_channel(topic)
    return channel['persisted']

def recall_message(topic):
    recalled = recall(topic)
    if recalled:
        return recalled[1]
    return None

def forget(topic):
    channel = _get_channel(topic)
    channel['persisted'] = None

class SwitchLink():
    def __init__(self, topic_in, topic_out, enable_topic, start_enable = True):
        subscribe(topic_in, self._link)
        apply(enable_topic, self.enable)
        self.topic_out = topic_out
        self.enable = start_enable

    def _link(self, topic, message, source):
        if self.enable:
            publish(self.topic_out, message, source)

    def enable(self, message):
        self.enable = message
        
        
        

