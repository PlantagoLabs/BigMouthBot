import asyncio

_subscribers = {}

def subscribe(topic, callback):
    subs = _subscribers.setdefault(topic, [])
    subs.append(callback)

def publish(topic, message, source = None):
    subs = _subscribers.get(topic)
    if not subs:
        return

    for sub in subs:
        sub(topic, message, source)

async def _survey_task(topic, msg_function, period_ms, source):
    while 1:
        data = msg_function()
        if data is not None:
            publish(topic, data, source)
        await asyncio.sleep_ms(period_ms)

def survey(topic, msg_function, period_ms, source = None):
    asyncio.create_task(_survey_task(topic, msg_function, period_ms, source))

def apply(topic, act_function):
    subscribe(topic, lambda x, y, z: act_function(y) if y is not None else act_function())
