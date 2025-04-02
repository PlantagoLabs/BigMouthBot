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
        publish(topic, msg_function(), source)
        await asyncio.sleep_ms(period_ms)

def survey(topic, msg_function, period_ms, source = None):
    asyncio.create_task(_survey_task(topic, msg_function, period_ms, source))

